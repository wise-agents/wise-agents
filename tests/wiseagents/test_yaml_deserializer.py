from wiseagents import WiseAgent
from wiseagents.llm.LangChainWiseAgentRemoteLLM import LangChainWiseAgentRemoteLLM
from wiseagents.llm.WiseAgentRemoteLLM import WiseAgentRemoteLLM
import yaml
import logging, pathlib

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
    assert deserialized_agent.llm.model_name =="Phi-3-mini-4k-instruct-q4.gguf"
    assert deserialized_agent.llm.remote_address == "http://localhost:8001/v1"
    logging.debug(deserialized_agent)
    response = deserialized_agent.llm.process("Hello my name is Stefano")
    assert response.content.__len__() > 0
    
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
    assert deserialized_agent[0].llm.model_name =="Phi-3-mini-4k-instruct-q4.gguf"
    assert deserialized_agent[0].llm.remote_address == "http://localhost:8001/v1"
    response = deserialized_agent[0].llm.process("Hello my name is Stefano")
    assert response.content.__len__() > 0
    
    logging.debug(deserialized_agent[1])
    
    assert isinstance(deserialized_agent[1], WiseAgent)
    assert deserialized_agent[1].name == "Agent2"
    assert deserialized_agent[1].description == "This is another test agent"
    assert deserialized_agent[1].llm.system_message == "Answer my greeting saying Hello and my name"
    assert deserialized_agent[1].llm.model_name =="Phi-3-mini-4k-instruct-q4.gguf"
    assert deserialized_agent[1].llm.remote_address == "http://localhost:8001/v1"
    response = deserialized_agent[1].llm.process("Hello my name is Stefano")
    assert response.content.__len__() > 0
    