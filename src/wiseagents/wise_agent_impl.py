import logging
from typing import Callable, Optional
from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentTransport
from wiseagents.llm.wise_agent_LLM import WiseAgentLLM
from wiseagents.transports.stomp import StompWiseAgentTransport


class PassThroughClientAgent(WiseAgent):
    '''This agent is used mainly for test purposes. It just passes the request to another agent and sends back the response to the client.'''
    '''Use Stomp protocol'''
    yaml_tag = u'!wiseagents.PassThroughClientAgent'
    def __init__(self, name, description , transport):
        self._name = name
        super().__init__(name=name, description=description, transport=transport, llm=None)
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(name={self.name}, description={self.description})"
    def process_request(self, request):
        #print(f"CA Request received: {request}")
        #just pass to the ohther agent
        self.send_request(WiseAgentMessage(request, self.name), 'WiseIntelligentAgent' )
        return True
    def process_response(self, response):
        #print(f"CA Response received: {response}")
        #send back response to the client
        self.response_delivery(response)
        return True
    def process_event(self, event):
        return True
    def process_error(self, error):
        return True
    def get_recipient_agent_name(self, message):
        return self.name
    def stop(self):
        pass
    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name
    @property
    def response_delivery(self) -> Optional[Callable[[], WiseAgentMessage]]:
        return self._response_delivery
    def set_response_delivery(self, response_delivery: Callable[[], WiseAgentMessage]):
        self._response_delivery = response_delivery
class LLMOnlyWiseAgent(WiseAgent):
    '''This agent implementation is used to test the LLM only agent.'''
    '''Use Stomp protocol''' 
    yaml_tag = u'!wiseagents.LLMOnlyWiseAgent'
    def __init__(self, name: str, description: str, llm : WiseAgentLLM, trasport: WiseAgentTransport):
        self._name = name
        self._description = description
        self._transport = trasport
        llm_agent = llm
        super().__init__(name=name, description=description, transport=self.transport, llm=llm_agent)

    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm}, transport={self.transport})"
        
    def process_event(self, event):
        return True
    def process_error(self, error):
        logging.error(error)
        return True
    def process_request(self, request: WiseAgentMessage):
        #print(f"IA Request received: {request}")
        llm_response = self.llm.process(request.message)
        self.send_response(WiseAgentMessage(llm_response.content, self.name), request.sender )
        return True
    def process_response(self, response : WiseAgentMessage):
        #print(f"Response received: {response}")
        return True
    def get_recipient_agent_name(self, message):
        return self.name
    def stop(self):
        pass    
    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name