import pytest

from wiseagents import WiseAgent, WiseAgentRegistry
from wiseagents.llm import WiseAgentRemoteLLM
from wiseagents.graphdb import LangChainWiseAgentGraphDB, Neo4jLangChainWiseAgentGraphDB
import yaml
import logging, pathlib

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    WiseAgentRegistry.clear_agents()
    WiseAgentRegistry.clear_contexts()

@pytest.mark.needsllm
def test_using_deserialized_agent():
    # Create a WiseAgent object
    with open(pathlib.Path().resolve() / "tests/wiseagents/test.yaml") as stream:
        try:
            deserialized_agent = yaml.load(stream, Loader=yaml.Loader)
        except yaml.YAMLError as exc:
            print(exc)
    # Assert that the serialized agent can be deserialized back to a WiseAgent object

    assert isinstance(deserialized_agent, WiseAgent)
    assert deserialized_agent.name == "Agent1"
    assert deserialized_agent.description == "This is a test agent"
    assert deserialized_agent.llm.system_message == "Answer my greeting saying Hello and my name"
    assert deserialized_agent.llm.model_name == "Phi-3-mini-4k-instruct-q4.gguf"
    assert deserialized_agent.llm.remote_address == "http://localhost:8001/v1"
    logging.debug(deserialized_agent)
    response = deserialized_agent.llm.process_single_prompt("Hello my name is Stefano")
    assert response.content.__len__() > 0
    assert deserialized_agent.graph_db.url == "bolt://localhost:7687"
    assert not deserialized_agent.graph_db.refresh_graph_schema
    assert deserialized_agent.graph_db.embedding_model_name == "all-MiniLM-L6-v2"
    assert deserialized_agent.vector_db.connection_string == "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
    assert deserialized_agent.vector_db.embedding_model_name == "all-MiniLM-L6-v2"


@pytest.mark.skip(reason="does not pass CI/CD")
def test_using_multiple_deserialized_agents():
    # Create a WiseAgent object
    deserialized_agent = []
    with open(pathlib.Path().resolve() / "tests/wiseagents/test-multiple.yaml") as stream:
        try:
            for agent in yaml.load_all(stream, Loader=yaml.Loader):
                deserialized_agent.append(agent)
        except yaml.YAMLError as exc:
            print(exc)
    # Assert that the serialized agent can be deserialized back to a WiseAgent object
    logging.debug(deserialized_agent)

    #assert isinstance(deserialized_agent[0], WiseAgent)
    assert deserialized_agent[0].name == "Agent1"
    assert deserialized_agent[0].description == "This is a test agent"
    assert deserialized_agent[0].llm.system_message == "Answer my greeting saying Hello and my name"
    assert deserialized_agent[0].llm.model_name == "Phi-3-mini-4k-instruct-q4.gguf"
    assert deserialized_agent[0].llm.remote_address == "http://localhost:8001/v1"
    response = deserialized_agent[0].llm.process("Hello my name is Stefano")
    assert response.content.__len__() > 0
    assert deserialized_agent[0].graph_db.url == "bolt://localhost:7687"
    assert not deserialized_agent[0].graph_db.refresh_graph_schema
    assert deserialized_agent[0].graph_db.embedding_model_name == "all-MiniLM-L6-v2"
    assert deserialized_agent[0].vector_db.connection_string == "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
    assert deserialized_agent[0].vector_db.embedding_model_name == "all-MiniLM-L6-v2"
    logging.debug(deserialized_agent[1])

    assert isinstance(deserialized_agent[1], WiseAgent)
    assert deserialized_agent[1].name == "Agent2"
    assert deserialized_agent[1].description == "This is another test agent"
    assert deserialized_agent[1].llm.system_message == "Answer my greeting saying Hello and my name"
    assert deserialized_agent[1].llm.model_name == "Phi-3-mini-4k-instruct-q4.gguf"
    assert deserialized_agent[1].llm.remote_address == "http://localhost:8001/v1"
    response = deserialized_agent[1].llm.process_single_prompt("Hello my name is Stefano")
    assert response.content.__len__() > 0
    assert deserialized_agent[1].graph_db.url == "bolt://localhost:7687"
    assert not deserialized_agent[1].graph_db.refresh_graph_schema
    assert deserialized_agent[1].vector_db.connection_string == "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
