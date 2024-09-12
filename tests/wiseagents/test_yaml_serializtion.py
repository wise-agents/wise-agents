from wiseagents.vectordb import PGVectorLangChainWiseAgentVectorDB

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentRegistry, WiseAgentTransport
from wiseagents.graphdb import Neo4jLangChainWiseAgentGraphDB
from wiseagents.llm import OpenaiAPIWiseAgentLLM
import yaml
import logging
import pytest

from wiseagents.transports import StompWiseAgentTransport

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    WiseAgentRegistry.clear_agents()
    WiseAgentRegistry.clear_contexts()
class DummyTransport(WiseAgentTransport):
    def __init__(self):
        pass

    def send_request(self, message: WiseAgentMessage, dest_agent_name: str):
        return super().send_request(message, dest_agent_name)
        pass

    def send_response(self, message: WiseAgentMessage, dest_agent_name: str):
        pass

    def start(self):
        pass

    def stop(self):
        pass


def test_serialize_wise_agent(monkeypatch):
    # Create a WiseAgent object
    agent_llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                            model_name="Phi-3-mini-4k-instruct-q4.gguf")
    agent_graph_db = Neo4jLangChainWiseAgentGraphDB(url="bolt://localhost:7687", refresh_graph_schema=False,
                                                    embedding_model_name="all-MiniLM-L6-v2", collection_name="test-cli-vector-db",
                                                    properties=["name", "type"])
    agent_vector_db = PGVectorLangChainWiseAgentVectorDB(
        connection_string="postgresql+psycopg://langchain:langchain@localhost:6024/langchain",
        embedding_model_name="all-MiniLM-L6-v2")
    agent = WiseAgent(name="Agent1", description="This is a test agent", transport=DummyTransport(), llm=agent_llm,
                      graph_db=agent_graph_db, vector_db=agent_vector_db)

    # Serialize the WiseAgent object to YAML
    serialized_agent = yaml.dump(agent)

    # Assert that the serialized agent is not empty
    assert serialized_agent is not None

    # Assert that the serialized agent is a string
    assert isinstance(serialized_agent, str)
    logging.debug(serialized_agent)

    # Assert that the serialized agent can be deserialized back to a WiseAgent object
    deserialized_agent = yaml.load(serialized_agent, Loader=yaml.Loader)
    assert isinstance(deserialized_agent, WiseAgent)
    assert deserialized_agent.name == agent.name
    assert deserialized_agent.description == agent.description
    assert deserialized_agent.llm.system_message == agent.llm.system_message
    assert deserialized_agent.llm.model_name == agent.llm.model_name
    assert deserialized_agent.llm.remote_address == "http://localhost:8001/v1"
    assert deserialized_agent.graph_db.url == "bolt://localhost:7687"
    assert deserialized_agent.graph_db.collection_name == "test-cli-vector-db"
    assert deserialized_agent.graph_db.properties == ["name", "type"]
    assert not deserialized_agent.graph_db.refresh_graph_schema
    assert deserialized_agent.graph_db.embedding_model_name == "all-MiniLM-L6-v2"
    assert deserialized_agent.vector_db.connection_string == "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
    assert deserialized_agent.vector_db.embedding_model_name == "all-MiniLM-L6-v2"
    logging.debug(deserialized_agent)


@pytest.mark.needsllm
def test_using_deserialized_agent(monkeypatch):
    # Create a WiseAgent object
    agent_llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                            model_name="Phi-3-mini-4k-instruct-q4.gguf")
    agent_graph_db = Neo4jLangChainWiseAgentGraphDB(url="bolt://localhost:7687", refresh_graph_schema=False,
                                                    embedding_model_name="all-MiniLM-L6-v2", collection_name="test-cli-vector-db",
                                                    properties=["name", "type"])
    agent_vector_db = PGVectorLangChainWiseAgentVectorDB(
        connection_string="postgresql+psycopg://langchain:langchain@localhost:6024/langchain",
        embedding_model_name="all-MiniLM-L6-v2")
    agent = WiseAgent(name="Agent1", description="This is a test agent", transport=DummyTransport(), llm=agent_llm,
                      graph_db=agent_graph_db,
                      vector_db=agent_vector_db)

    # Serialize the WiseAgent object to YAML
    serialized_agent = yaml.dump(agent)

    # Assert that the serialized agent is not empty
    assert serialized_agent is not None

    # Assert that the serialized agent is a string
    assert isinstance(serialized_agent, str)
    logging.debug(serialized_agent)

    # Assert that the serialized agent can be deserialized back to a WiseAgent object
    deserialized_agent = yaml.load(serialized_agent, Loader=yaml.Loader)
    assert isinstance(deserialized_agent, WiseAgent)
    assert deserialized_agent.name == agent.name
    assert deserialized_agent.description == agent.description
    assert deserialized_agent.llm.system_message == agent.llm.system_message
    assert deserialized_agent.llm.model_name == agent.llm.model_name
    assert deserialized_agent.llm.remote_address == "http://localhost:8001/v1"
    assert deserialized_agent.graph_db.collection_name == "test-cli-vector-db"
    assert deserialized_agent.graph_db.properties == ["name", "type"]
    assert deserialized_agent.graph_db.url == "bolt://localhost:7687"
    assert not deserialized_agent.graph_db.refresh_graph_schema
    assert deserialized_agent.graph_db.embedding_model_name == "all-MiniLM-L6-v2"
    logging.debug(deserialized_agent)
    response = deserialized_agent.llm.process_single_prompt("Hello my name is Stefano")
    assert response.content.__len__() > 0
    assert deserialized_agent.vector_db.connection_string == "postgresql+psycopg://langchain:langchain@localhost:6024/langchain"
    assert deserialized_agent.vector_db.embedding_model_name == "all-MiniLM-L6-v2"
