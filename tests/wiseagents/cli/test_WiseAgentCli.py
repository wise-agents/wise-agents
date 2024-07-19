import os

import pytest
from wiseagents.vectordb import Document, PGVectorLangChainWiseAgentVectorDB
from wiseagents.cli.wise_agent_cli import main

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    original_postgres_user = set_env_variable("POSTGRES_USER", "postgres")
    original_postgres_password = set_env_variable("POSTGRES_PASSWORD", "postgres")
    original_postgres_db = set_env_variable("POSTGRES_DB", "postgres")
    original_stomp_user = set_env_variable("STOMP_USER", "artemis")
    original_stomp_password = set_env_variable("STOMP_PASSWORD", "artemis")

    pg_vector_db = PGVectorLangChainWiseAgentVectorDB(get_connection_string())
    pg_vector_db.delete_collection("wise-agents-collection")
    pg_vector_db.insert_documents([Document(content="The Boston Celtics won the NBA Finals in 2024",
                                            metadata={"source": "nba.com"}),
                                   Document(content="The Florida Panthers won the NHL Playoffs in 2024",
                                            metadata={"source": "countries.com"})
                                   ],
                                  "wise-agents-collection")

    yield
    pg_vector_db.delete_collection("wise-agents-collection")

    # Clean up environment variables
    reset_env_variable("POSTGRES_USER", original_postgres_user)
    reset_env_variable("POSTGRES_PASSWORD", original_postgres_password)
    reset_env_variable("POSTGRES_DB", original_postgres_db)
    reset_env_variable("STOMP_USER", original_stomp_user)
    reset_env_variable("STOMP_PASSWORD", original_stomp_password)


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


def test_cli_with_rag_agent(monkeypatch, pytestconfig, capsys):
    project_root = pytestconfig.rootpath

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
