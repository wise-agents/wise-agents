from wiseagents import WiseAgent
from wiseagents.graphdb import Neo4jLangChainWiseAgentGraphDB
from wiseagents.llm.LangChainWiseAgentRemoteLLM import LangChainWiseAgentRemoteLLM
from wiseagents.llm.WiseAgentRemoteLLM import WiseAgentRemoteLLM
import yaml
import logging


def test_serialize_wise_agent(monkeypatch):
    # Create a WiseAgent object
    agent_llm = LangChainWiseAgentRemoteLLM(system_message="Answer my greeting saying Hello and my name",
                                            model_name="Phi-3-mini-4k-instruct-q4.gguf")
    agent_graph_db = Neo4jLangChainWiseAgentGraphDB("bolt://localhost:7687", False)
    agent = WiseAgent(name="Agent1", description="This is a test agent", llm=agent_llm, graph_db=agent_graph_db)

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
    assert not deserialized_agent.graph_db.refresh_graph_schema
    logging.debug(deserialized_agent)


def test_using_deserialized_agent(monkeypatch):
    # Create a WiseAgent object
    agent_llm = LangChainWiseAgentRemoteLLM(system_message="Answer my greeting saying Hello and my name",
                                            model_name="Phi-3-mini-4k-instruct-q4.gguf")
    agent_graph_db = Neo4jLangChainWiseAgentGraphDB("bolt://localhost:7687", False)
    agent = WiseAgent(name="Agent1", description="This is a test agent", llm=agent_llm, graph_db=agent_graph_db)

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
    assert not deserialized_agent.graph_db.refresh_graph_schema
    logging.debug(deserialized_agent)
    response = deserialized_agent.llm.process("Hello my name is Stefano")
    assert response.content.__len__() > 0
