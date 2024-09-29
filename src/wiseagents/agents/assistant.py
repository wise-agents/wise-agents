
import logging
from threading import Thread
import threading
import time
from typing import Callable, List, Optional
import uuid

from openai.types.chat import ChatCompletionMessageParam
from wiseagents import WiseAgent, WiseAgentCollaborationType, WiseAgentMetaData, WiseAgentRegistry, WiseAgentTransport
from wiseagents.wise_agent_messaging import WiseAgentMessage
import gradio

class AssistantAgent(WiseAgent):
    """
    This utility agent start a web interface and pass the user input to another agent.
    The web interface will be running at http://127.0.0.1:7860
    """
    yaml_tag = u'!wiseagents.agents.AssistantAgent'
    
    _response_delivery = None
    _cond = threading.Condition()
    _response : WiseAgentMessage = None
    _ctx = None
    
    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        return obj

    def __init__(self, name: str, metadata: WiseAgentMetaData , transport: WiseAgentTransport,
                 destination_agent_name: str):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            transport (WiseAgentTransport): the transport to use for communication
            destination_agent_name (str): the name of the agent to send requests to
        """
        self._name = name
        self._destination_agent_name = destination_agent_name
        super().__init__(name=name, metadata=metadata, transport=transport, llm=None)

    def __repr__(self):
        """Return a string representation of the agent."""
        return f"{self.__class__.__name__}(name={self.name}, \
            metadata={self.metadata}, transport={self.transport}, \
            destination_agent_name={self.destination_agent_name},\
            response_delivery={self.response_delivery}"
    
    def start_agent(self):
        super().start_agent()
        self._ctx = f'{self.name}.{str(uuid.uuid4())}'
        WiseAgentRegistry.create_context(self._ctx).set_collaboration_type(WiseAgentCollaborationType.CHAT)
        gradio.ChatInterface(self.slow_echo).launch(prevent_thread_lock=True)
    
    def stop_agent(self):
        super().stop_agent()
        WiseAgentRegistry.remove_context(self._ctx)

    def slow_echo(self, message, history):
            with self._cond:
                self.handle_request(WiseAgentMessage(message=message, sender=self.name, context_name=self._ctx))
                self._cond.wait()
                return self._response.message

    def process_request(self, request: WiseAgentMessage,
                        conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
        """
        Process a request message by just passing it to another agent.

        Args:
            request (WiseAgentMessage): the request message to process
            conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.

        Returns:
            Optional[str]: the response to the request message as a string or None if there is
            no string response yet
        """
        print(f"AssistantAgent: process_request: {request}")
        WiseAgentRegistry.get_context(request.context_name).append_chat_completion({"role": "user", "content": request.message})
        self.send_request(request, self.destination_agent_name)
        return None

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
