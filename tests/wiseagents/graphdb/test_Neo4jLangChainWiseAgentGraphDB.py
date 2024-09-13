import os

import pytest

from wiseagents.graphdb import Entity, GraphDocument, Neo4jLangChainWiseAgentGraphDB, Relationship, Source

collection_name = "test-vector-db"
@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    # Ensure that nothing exists the graph DB
    original_neo4j_username = os.environ.get("NEO4J_USERNAME")
    os.environ["NEO4J_USERNAME"] = "neo4j"
    original_neo4j_password = os.environ.get("NEO4J_PASSWORD")
    os.environ["NEO4J_PASSWORD"] = "neo4jpassword"
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)
    graph_db.query("MATCH (n)-[r]-() DELETE r")
    graph_db.query("MATCH (n) DELETE n")

    yield

    # Delete all relationships and entities from graph_db
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)
    graph_db.query("MATCH (n)-[r]-() DELETE r")
    graph_db.query("MATCH (n) DELETE n")
    graph_db.delete_vector_db()
    graph_db.close()

    # Clean up environment variables
    if original_neo4j_username is None:
        del os.environ["NEO4J_USERNAME"]
    else:
        os.environ["NEO4J_USERNAME"] = original_neo4j_username
    if original_neo4j_password is None:
        del os.environ["NEO4J_PASSWORD"]
    else:
        os.environ["NEO4J_PASSWORD"] = original_neo4j_password


def set_env(monkeypatch):
    """
        This test requires a running Neo4j instance on bolt://localhost:7687. The required
        graph database can be started using the run_graphdb.sh script.
    """
    monkeypatch.setenv("NEO4J_USERNAME", "neo4j")
    assert os.environ.get("NEO4J_USERNAME") == "neo4j"
    monkeypatch.setenv("NEO4J_PASSWORD", "neo4jpassword")
    assert os.environ.get("NEO4J_PASSWORD") == "neo4jpassword"


def test_insert_graph_documents_and_query(monkeypatch):
    set_env(monkeypatch)
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)

    try:
        page_content = "The CN Tower is located in Toronto, a major city in Ontario. Ontario is a province in Canada."
        landmark = Entity(id="1", metadata={"name": "CN Tower", "type": "landmark"})
        city = Entity(id="2", metadata={"name": "Toronto", "type": "city"})
        province = Entity(id="3", metadata={"name": "Ontario", "type": "province"})
        country = Entity(id="4", metadata={"name": "Canada", "type": "country"})
        graph_document = GraphDocument(entities=[landmark, city, province, country],
                                       relationships=[Relationship(source=landmark, target=city, label="is located in"),
                                                      Relationship(source=city, target=province,
                                                                   label="is in the province of"),
                                                      Relationship(source=province, target=country,
                                                                   label="is in the country of")],
                                       source=Source(content=page_content))
        graph_db.insert_graph_documents([graph_document])
        graph_db.refresh_schema()
        assert graph_db.get_schema() != ""

        result = graph_db.query("MATCH (n:entity {name: 'CN Tower'})"
                                "-[:IS_LOCATED_IN]->(city:entity)"
                                "-[:IS_IN_THE_PROVINCE_OF]->(province:entity)"
                                "-[:IS_IN_THE_COUNTRY_OF]->(country:entity)"
                                "RETURN country.name AS Country")
        assert result == [{'Country': 'Canada'}]

        documents = graph_db.query_with_embeddings("tall building", 1)
        assert "CN Tower" in documents[0].content

        documents = graph_db.query_with_embeddings(query="tall building", k=1, params={"extra": "ParamInfo"},
                                                   metadata_filter={"type": "landmark"})
        assert "CN Tower" in documents[0].content

        documents = graph_db.query_with_embeddings(query="tall building", k=1, params={"extra": "ParamInfo"},
                                                   metadata_filter={"type": "country"})
        assert "CN Tower" not in documents[0].content

        documents = graph_db.query_with_embeddings("province", 1)
        assert "Ontario" in documents[0].content
    finally:
        graph_db.close()
        


def test_insert_entity_and_query(monkeypatch):
    set_env(monkeypatch)
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)

    try:
        page_content = ""
        graph_db.insert_entity(Entity(id="5", metadata={"name": "USA", "type": "country"}),
                               Source(content=page_content))
        graph_db.refresh_schema()
        assert graph_db.get_schema() != ""

        result = graph_db.query("MATCH (c:entity {name: 'USA'})"
                                "RETURN c.name AS Country")
        assert result == [{'Country': 'USA'}]
    finally:
        graph_db.close()


def test_insert_relationship_and_query(monkeypatch):
    set_env(monkeypatch)
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)

    try:
        page_content = "Ottawa is the capital of Canada."
        country = Entity(id="4", metadata={"name": "Canada", "type": "country"})
        graph_db.insert_entity(country, Source(content=page_content))
        capital = Entity(id="6", metadata={"name": "Ottawa", "type": "city"})
        graph_db.insert_entity(capital, Source(content=page_content))

        capital_of = Relationship(label="is_the_capital_of", source=capital, target=country)
        graph_db.insert_relationship(capital_of, Source(content=page_content))
        graph_db.refresh_schema()
        assert graph_db.get_schema() != ""

        result = graph_db.query("MATCH (c:entity {name: 'Ottawa'})"
                                "-[:IS_THE_CAPITAL_OF]->(country:entity)"
                                "RETURN country.name AS Country")
        assert result == [{'Country': 'Canada'}]

        documents = graph_db.query_with_embeddings("capital", 1)
        assert "Ottawa" in documents[0].content
    finally:
        graph_db.close()
