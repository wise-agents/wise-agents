import logging

import pytest
import yaml

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentMessageType, WiseAgentRegistry, WiseAgentTransport
from wiseagents.agents import AssistantAgent
from wiseagents.graphdb import Neo4jLangChainWiseAgentGraphDB
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.vectordb import PGVectorLangChainWiseAgentVectorDB
from wiseagents.yaml import WiseAgentsLoader

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield

class DummyTransport(WiseAgentTransport):
    yaml_tag = "!tests.wiseagents.test_yaml_serializtion.DummyTransport"
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

class TestSerializationAgent(WiseAgent):
    yaml_tag = "!tests.wiseagents.test_yaml_serializtion.TestSerializationAgent"
    def __init__(self, name, description, transport, llm=None, graph_db=None, vector_db=None):
        super().__init__(name, description, transport, llm=llm, graph_db=graph_db, vector_db=vector_db)

def test_serialize_wise_agent(monkeypatch):
    try:
        # Create a WiseAgent object
        agent_llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                                model_name="Phi-3-mini-4k-instruct-q4.gguf")
        agent_graph_db = Neo4jLangChainWiseAgentGraphDB(url="bolt://localhost:7687", refresh_graph_schema=False,
                                                        embedding_model_name="all-MiniLM-L6-v2", collection_name="test-cli-vector-db",
                                                        properties=["name", "type"])
        agent_vector_db = PGVectorLangChainWiseAgentVectorDB(
            connection_string="postgresql+psycopg://langchain:langchain@localhost:6024/langchain",
            embedding_model_name="all-MiniLM-L6-v2")
        agent = TestSerializationAgent(name="Agent1", description="This is a test agent", transport=DummyTransport(), llm=agent_llm,
                        graph_db=agent_graph_db, vector_db=agent_vector_db)

        # Serialize the WiseAgent object to YAML
        serialized_agent = yaml.dump(agent)
    finally:
        agent.stop_agent()
    try:
        # Assert that the serialized agent is not empty
        assert serialized_agent is not None

        # Assert that the serialized agent is a string
        assert isinstance(serialized_agent, str)
        logging.debug(serialized_agent)

        # Assert that the serialized agent can be deserialized back to a WiseAgent object
        deserialized_agent = yaml.load(serialized_agent, Loader=WiseAgentsLoader)
        assert isinstance(deserialized_agent, TestSerializationAgent)
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
    finally:
        deserialized_agent.stop_agent()


@pytest.mark.needsllm
def test_using_deserialized_agent(monkeypatch):
    try:
        # Create a WiseAgent object
        agent_llm = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name",
                                                model_name="Phi-3-mini-4k-instruct-q4.gguf")
        agent_graph_db = Neo4jLangChainWiseAgentGraphDB(url="bolt://localhost:7687", refresh_graph_schema=False,
                                                        embedding_model_name="all-MiniLM-L6-v2", collection_name="test-cli-vector-db",
                                                        properties=["name", "type"])
        agent_vector_db = PGVectorLangChainWiseAgentVectorDB(
            connection_string="postgresql+psycopg://langchain:langchain@localhost:6024/langchain",
            embedding_model_name="all-MiniLM-L6-v2")
        agent = TestSerializationAgent(name="Agent1", description="This is a test agent", transport=DummyTransport(), llm=agent_llm,
                        graph_db=agent_graph_db,
                        vector_db=agent_vector_db)

        # Serialize the WiseAgent object to YAML
        serialized_agent = yaml.dump(agent)
    finally:
        agent.stop_agent()
    try:
        # Assert that the serialized agent is not empty
        assert serialized_agent is not None

        # Assert that the serialized agent is a string
        assert isinstance(serialized_agent, str)
        logging.debug(serialized_agent)

        # Assert that the serialized agent can be deserialized back to a WiseAgent object
        deserialized_agent = yaml.load(serialized_agent, Loader=WiseAgentsLoader)
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
    finally:
        deserialized_agent.stop_agent()

def test_serialize_assistant():
    try:
        assistant = AssistantAgent(name="Assistant1", description="This is a test assistant", transport=DummyTransport(), destination_agent_name="")
        serialized_assistant = yaml.dump(assistant)
        logging.info(serialized_assistant)
        deserialized_agent = yaml.load(serialized_assistant, Loader=WiseAgentsLoader)
    finally:
        assistant.stop_agent()

def test_serialize_message():
    message = WiseAgentMessage(message="Hello", 
                               sender="Agent1", 
                               message_type=WiseAgentMessageType.ACK,
                               chat_id="12345", 
                               tool_id="WeatherAgent", 
                               context_name="Weather", 
                               route_response_to="Agent1")
    with open("test_message.yaml", "w") as stream:
        yaml.dump(message, stream)
    
