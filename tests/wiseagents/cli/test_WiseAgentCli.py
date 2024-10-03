import os
import sys

import pytest

from wiseagents import WiseAgentRegistry
from wiseagents.cli.wise_agent_cli import main
from wiseagents.graphdb import Entity, GraphDocument, Neo4jLangChainWiseAgentGraphDB, Relationship, Source
from wiseagents.vectordb import Document, PGVectorLangChainWiseAgentVectorDB
from tests.wiseagents import assert_standard_variables_set, mock_open_ai_for_ci, mock_open_ai_chat_completion, get_user_messages

def __mock_llm(*args, **kwargs):
    user_messages = get_user_messages(kwargs["messages"])
    if "Who won the NBA championship in 2024?" in user_messages[0]:
        return mock_open_ai_chat_completion("The Boston Celtics won the NBA Championship in 2024.")
    elif "Fictitious Tower is located in Canada" in user_messages[0]:
        return mock_open_ai_chat_completion(
            "Fictitious Tower doesn't exist, but if it did, it would be in Canada.")
    return mock_open_ai_chat_completion("The Boston Celtics won the NBA Finals in 2024")

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    assert_standard_variables_set()

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


def get_connection_string():
    return f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@localhost:6024/{os.environ['POSTGRES_DB']}"


@pytest.mark.needsllm
def test_cli_with_rag_agent(monkeypatch, pytestconfig, capsys, mocker):
    mock_open_ai_for_ci(mocker, __mock_llm)
    inputs = ['/load-agents', '', '/send', 'RAGWiseAgent1', 'Who won the NBA championship in 2024?', '/exit']

    def mock_input(prompt):
        if inputs:
            response = inputs.pop(0)
            print(prompt + response)
            return response
        else:
            raise TimeoutError("No input provided in time or inputs list is empty")

    monkeypatch.setattr('builtins.input', mock_input)
    #removing any arguments passed to the test (otherwise for example it fails with -k {test_name})
    sys.argv = sys.argv[:1]
    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    print(captured.out)
    print(captured.err)
    assert "Boston Celtics" in captured.out


@pytest.mark.needsllm
def test_cli_with_graph_rag_agent(monkeypatch, pytestconfig, capsys, mocker):
    mock_open_ai_for_ci(mocker, __mock_llm)
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
