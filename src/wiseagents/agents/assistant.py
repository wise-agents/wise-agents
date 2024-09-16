
import logging
from threading import Thread
import threading
import time
from typing import Callable, Optional

from wiseagents import WiseAgent, WiseAgentTransport
from wiseagents.wise_agent_messaging import WiseAgentMessage
import gradio

class AssistantAgent(WiseAgent):
    """
    This utility agent simply passes a request that it receives to another agent and sends the
    response back to the client.
    """
    yaml_tag = u'!wiseagents.agents.AssistantAgent'
    
    _response_delivery = None
    _cond = threading.Condition()
    _response : WiseAgentMessage = None
    
    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        return obj

    def __init__(self, name: str, description: str , transport: WiseAgentTransport,
                 destination_agent_name: str):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            description (str): a description of the agent
            transport (WiseAgentTransport): the transport to use for communication
            destination_agent_name (str): the name of the agent to send requests to
        """
        self._name = name
        self._destination_agent_name = destination_agent_name
        super().__init__(name=name, description=description, transport=transport, llm=None)

    def __repr__(self):
        """Return a string representation of the agent."""
        return f"{self.__class__.__name__}(name={self.name}, \
            description={self.description}, transport={self.transport}, \
            destination_agent_name={self.destination_agent_name},\
            response_delivery={self.response_delivery}"
    
    def start_agent(self):
        super().start_agent()
        gradio.ChatInterface(self.slow_echo).launch(prevent_thread_lock=True)

    def slow_echo(self, message, history):
            with self._cond:
                self.process_request(WiseAgentMessage(message, self.name))
                self._cond.wait()
                return self._response.message

    def process_request(self, request: WiseAgentMessage):
        """Process a request message by just passing it to another agent."""
        print(f"AssistantAgent: process_request: {request}")
        self.send_request(request, self.destination_agent_name)
        return True

    def process_response(self, response : WiseAgentMessage):
        """Process a response message just sending it back to the client."""
        print(f"AssistantAgent: process_response: {response}")
        with self._cond:
            self._response = response
            self._cond.notify()
        return True

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Do nothing"""
        return True

    def get_recipient_agent_name(self, message):
        """Return the name of the agent to send the message to."""
        return self.name

    def stop(self):
        """Do nothing"""
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def destination_agent_name(self) -> str:
        """Get the name of the agent to send requests to."""
        return self._destination_agent_name

    @property
    def response_delivery(self) -> Optional[Callable[[], WiseAgentMessage]]:
        """Get the function to deliver the response to the client.
        return (Callable[[], WiseAgentMessage]): the function to deliver the response to the client"""
        return self._response_delivery

    def set_response_delivery(self, response_delivery: Callable[[], WiseAgentMessage]):
        """
        Set the function to deliver the response to the client.

        Args:
            response_delivery (Callable[[], WiseAgentMessage]): the function to deliver the response to the client
        """
        self._response_delivery = response_delivery
