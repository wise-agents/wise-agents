import logging
import os
from time import sleep

import pytest

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentMetaData, WiseAgentRegistry
from wiseagents.transports import StompWiseAgentTransport


@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    
    

class WiseAgentDoingNothing(WiseAgent):
     
    request_received : WiseAgentMessage = None
    response_received : WiseAgentMessage = None
    
    def __init__(self, name: str, description: str):
        self._name = name
        self._description = description
        transport = StompWiseAgentTransport(host='localhost', port=61616, agent_name=self.name)
        super().__init__(name, WiseAgentMetaData(description), transport, None, None, None)
        
        
    def process_event(self, event):
        return True
    def process_error(self, error):
        logging.error(error)
        return True
    def handle_request(self, request: WiseAgentMessage):
        self.request_received = request
        self.send_response(WiseAgentMessage('I am doing nothing', self.name), request.sender )
        return True
    def process_response(self, response : WiseAgentMessage):
        self.response_received = response
        return True

    def stop(self):
        pass    
    


@pytest.mark.skip(reason="This works fine when run on its own, but fails when run with all the other tests")
def test_send_message_to_agent_and_get_response():
    os.environ['STOMP_USER'] = 'artemis'
    os.environ['STOMP_PASSWORD'] = 'artemis'
    
    
    agent1 = WiseAgentDoingNothing('Agent1', 'Agent1')
    agent2 = WiseAgentDoingNothing('Agent2', 'Agent2')
    
    agent1.send_request(WiseAgentMessage(message='Do Nothing', sender='Agent1'), dest_agent_name='Agent2')
    sleep(1)
    agent2.send_request(WiseAgentMessage(message='Do Nothing', sender='Agent2'), dest_agent_name='Agent1')
    sleep(1)
    
    
    
    assert agent2.request_received.message == 'Do Nothing'
    
    assert agent1.response_received.message == 'I am doing nothing'

    for  message in WiseAgentRegistry.get_or_create_context('default').message_trace:
        logging.debug(f'{message}')
    
    assert WiseAgentRegistry.get_or_create_context('default').message_trace[0].message == 'Do Nothing'
    assert WiseAgentRegistry.get_or_create_context('default').message_trace[0].sender == 'Agent1'
    assert WiseAgentRegistry.get_or_create_context('default').message_trace[1].message == 'I am doing nothing'
    assert WiseAgentRegistry.get_or_create_context('default').message_trace[1].sender == 'Agent2'
    assert WiseAgentRegistry.get_or_create_context('default').message_trace[2].message == 'Do Nothing'
    assert WiseAgentRegistry.get_or_create_context('default').message_trace[2].sender == 'Agent2'
    assert WiseAgentRegistry.get_or_create_context('default').message_trace[3].message == 'I am doing nothing'
    assert WiseAgentRegistry.get_or_create_context('default').message_trace[3].sender == 'Agent1'
    
    #stop all agents
    agent1.stop()
    agent2.stop()

    
    