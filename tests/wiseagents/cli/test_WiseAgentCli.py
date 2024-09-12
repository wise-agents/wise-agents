import os

import pytest
from wiseagents import WiseAgentRegistry
from wiseagents.graphdb import Entity, GraphDocument, Neo4jLangChainWiseAgentGraphDB, Relationship, Source

from wiseagents.vectordb import Document, PGVectorLangChainWiseAgentVectorDB
from wiseagents.cli.wise_agent_cli import main

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    original_postgres_user = set_env_variable("POSTGRES_USER", "postgres")
    original_postgres_password = set_env_variable("POSTGRES_PASSWORD", "postgres")
    original_postgres_db = set_env_variable("POSTGRES_DB", "postgres")
    original_stomp_user = set_env_variable("STOMP_USER", "artemis")
    original_stomp_password = set_env_variable("STOMP_PASSWORD", "artemis")
    original_neo4j_username = set_env_variable("NEO4J_USERNAME", "neo4j")
    original_neo4j_password = set_env_variable("NEO4J_PASSWORD", "neo4jpassword")

    # Vector DB set up
    pg_vector_db = PGVectorLangChainWiseAgentVectorDB(get_connection_string())
    pg_vector_db.delete_collection("wise-agents-collection")
    pg_vector_db.insert_documents([Document(content="The Boston Celtics won the NBA Finals in 2024",
                                            metadata={"source": "nba.com"}),
                                   Document(content="The Florida Panthers won the NHL Playoffs in 2024",
                                            metadata={"source": "countries.com"})
                                   ],
                                  "wise-agents-collection")

    # Graph DB setup
    collection_name = "test-cli-vector-db"
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)
    page_content = "The Fictitious Tower is located in Toronto, a major city in Ontario. Ontario is a province in Canada."
    landmark = Entity(id="1", metadata={"name": "Fictitious Tower", "type": "landmark"})
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
    yield

    # Vector DB clean up
    pg_vector_db.delete_collection("wise-agents-collection")

    # Graph DB clean up
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)
    graph_db.query("MATCH (n)-[r]-() DELETE r")
    graph_db.query("MATCH (n) DELETE n")
    graph_db.delete_vector_db()
    graph_db.close()

    # Clean up environment variables
    reset_env_variable("POSTGRES_USER", original_postgres_user)
    reset_env_variable("POSTGRES_PASSWORD", original_postgres_password)
    reset_env_variable("POSTGRES_DB", original_postgres_db)
    reset_env_variable("STOMP_USER", original_stomp_user)
    reset_env_variable("STOMP_PASSWORD", original_stomp_password)
    reset_env_variable("NEO4J_USERNAME", original_neo4j_username)
    reset_env_variable("NEO4J_PASSWORD", original_neo4j_password)
    
    WiseAgentRegistry.clear_agents()
    WiseAgentRegistry.clear_contexts()

def set_env_variable(env_variable: str, value: str) -> str:
    original_value = os.environ.get(env_variable)
    os.environ[env_variable] = value
    return original_value


def reset_env_variable(env_variable: str, original_value: str):
    if original_value is None:
        del os.environ[env_variable]
    else:
        os.environ[env_variable] = original_value


def get_connection_string():
    return f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@localhost:6024/{os.environ['POSTGRES_DB']}"


def set_env(monkeypatch):
    """
        This test requires a running pgvector instance. The required
        vector database can be started using the run_vectordb.sh script.
    """
    monkeypatch.setenv("POSTGRES_USER", "postgres")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres")
    monkeypatch.setenv("POSTGRES_DB", "postgres")


@pytest.mark.needsllm
def test_cli_with_rag_agent(monkeypatch, pytestconfig, capsys):
    inputs = ['/load-agents', '', '/send', 'RAGWiseAgent1', 'Who won the NBA championship in 2024?', '/exit']

    def mock_input(prompt):
        if inputs:
            response = inputs.pop(0)
            print(prompt + response)
            return response
        else:
            raise TimeoutError("No input provided in time or inputs list is empty")

    monkeypatch.setattr('builtins.input', mock_input)

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    print(captured.out)
    print(captured.err)
    assert "Boston Celtics" in captured.out


@pytest.mark.needsllm
def test_cli_with_graph_rag_agent(monkeypatch, pytestconfig, capsys):
    inputs = ['/load-agents', '', '/send', 'GraphRAGWiseAgent1', 'what country is the tall building located in', '/exit']

    def mock_input(prompt):
        if inputs:
            response = inputs.pop(0)
            print(prompt + response)
            return response
        else:
            raise TimeoutError("No input provided in time or inputs list is empty")

    monkeypatch.setattr('builtins.input', mock_input)

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    print(captured.out)
    print(captured.err)
    assert "Canada" in captured.out
