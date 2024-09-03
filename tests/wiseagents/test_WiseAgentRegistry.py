import logging

import pytest
from wiseagents import WiseAgent, WiseAgentContext, WiseAgentMessage, WiseAgentRegistry, WiseAgentTransport
from wiseagents.transports.stomp import StompWiseAgentTransport

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    WiseAgentRegistry.clear_agents()
    WiseAgentRegistry.clear_contexts()
class DummyTransport(WiseAgentTransport):
    
    def send_request(self, message: WiseAgentMessage, dest_agent_name: str):
        return super().send_request(message, dest_agent_name)
        pass
    def send_response(self, message: WiseAgentMessage, dest_agent_name: str):
        pass
    def start(self):
        pass
    def stop(self):
        pass
   
def test_register_agents():
    WiseAgentRegistry.clear_agents()
    agent = WiseAgent(name="Agent1", description="This is a test agent", 
                      transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="WiseIntelligentAgent")
                                 )
    assert 1 == WiseAgentRegistry.get_agents().__len__()
    logging.info(f'Agent ={agent}')
    logging.info(f'Agent in the registry={WiseAgentRegistry.get_agent(agent.name)}')
    assert agent == WiseAgentRegistry.get_agent(agent.name)

def test_remove_agent():
    agent_name = "Agent1"
    WiseAgentRegistry.remove_agent(agent_name)
    assert None == WiseAgentRegistry.get_agent(agent_name)

def test_get_agents():
    WiseAgentRegistry.clear_agents()
    agents = [WiseAgent(name="Agent1", description="This is a test agent", transport=DummyTransport()), 
              WiseAgent(name="Agent2", description="This is another test agent", transport=DummyTransport()), 
              WiseAgent(name="Agent3", description="This is yet another test agent", transport=DummyTransport())]
    
    for agent in agents:
        assert agent == WiseAgentRegistry.get_agent(agent.name)

def test_get_contexts():
    WiseAgentRegistry.clear_contexts()
    contexts = [WiseAgentContext(name="Context1"), 
              WiseAgentContext(name="Context2"), 
              WiseAgentContext(name="Context3")]
    
    for context in contexts:
        assert True == WiseAgentRegistry.does_context_exist(context.name)
        
def test_get_or_create_context():
    WiseAgentRegistry.clear_contexts()
    context = WiseAgentContext(name="Context1")
    WiseAgentRegistry.get_or_create_context(context.name)
    assert context == WiseAgentRegistry.get_or_create_context(context.name)