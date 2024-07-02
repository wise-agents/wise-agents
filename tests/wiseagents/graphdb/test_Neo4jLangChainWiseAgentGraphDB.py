import os

from wiseagents.graphdb.Entity import Entity
from wiseagents.graphdb.GraphDocument import GraphDocument
from wiseagents.graphdb.Neo4jLangChainWiseAgentGraphDB import Neo4jLangChainWiseAgentGraphDB
from wiseagents.graphdb.Relationship import Relationship
from wiseagents.graphdb.Source import Source


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
    graph_db = Neo4jLangChainWiseAgentGraphDB("bolt://localhost:7687", False)

    assert graph_db.get_schema() == ""

    page_content = "The CN Tower is located in Toronto, a major city in Ontario. Ontario is a province in Canada."
    landmark = Entity(id="CN Tower")
    city = Entity(id="Toronto")
    province = Entity(id="Ontario")
    country = Entity(id="Canada")
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

    result = graph_db.query("MATCH (n:entity {id: 'CN Tower'})"
                            "-[:IS_LOCATED_IN]->(city:entity)"
                            "-[:IS_IN_THE_PROVINCE_OF]->(province:entity)"
                            "-[:IS_IN_THE_COUNTRY_OF]->(country:entity)"
                            "RETURN country.id AS Country")

    assert result == [{'Country': 'Canada'}]

    graph_db.close()


def test_insert_entity_and_query(monkeypatch):
    set_env(monkeypatch)
    graph_db = Neo4jLangChainWiseAgentGraphDB("bolt://localhost:7687", False)

    assert graph_db.get_schema() == ""

    page_content = ""
    graph_db.insert_entity(Entity(id="USA"), Source(content=page_content))
    graph_db.refresh_schema()
    assert graph_db.get_schema() != ""

    result = graph_db.query("MATCH (c:entity {id: 'USA'})"
                            "RETURN c.id AS Country")

    assert result == [{'Country': 'USA'}]

    graph_db.close()


def test_insert_relationship_and_query(monkeypatch):
    set_env(monkeypatch)
    graph_db = Neo4jLangChainWiseAgentGraphDB("bolt://localhost:7687", False)

    assert graph_db.get_schema() == ""

    page_content = "Ottawa is the capital of Canada."
    capital_of = Relationship(label="is_the_capital_of", source=Entity(id="Ottawa"), target=Entity(id="Canada"))
    graph_db.insert_relationship(capital_of, Source(content=page_content))
    graph_db.refresh_schema()
    assert graph_db.get_schema() != ""

    result = graph_db.query("MATCH (c:entity {id: 'Ottawa'})"
                            "-[:IS_THE_CAPITAL_OF]->(country:entity)"
                            "RETURN country.id AS Country")

    assert result == [{'Country': 'Canada'}]

    graph_db.close()
