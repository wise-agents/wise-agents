from abc import *
from typing import Callable, Optional

from enum import Enum, auto

from yaml import YAMLObject


class WiseAgentMessageType(Enum):
    ALERT = auto()
    QUERY = auto()
    RESPONSE = auto()
    ACTION_REQUEST = auto()
    HUMAN = auto()
    
class WiseAgentEvent:
    """
    TODO
    """


class WiseAgentMessage(YAMLObject):
    yaml_tag = u'!wiseagents.WiseAgentMessage'
    def __init__(self, message: str, sender: Optional[str] = None, message_type: Optional[WiseAgentMessageType] = None, identifier: Optional[int] = None, context_name: Optional[str] = None):
        self._message = message
        self._sender = sender
        self._message_type = message_type
        if identifier is not None: 
            self._identifier = identifier
        else:
            self._identifier = id(self)
        if context_name is not None:
            self._context_name = context_name
        else:
            self._context_name = 'default'

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message}, sender={self.sender}, message_type={self.message_type}, id={self.identifier})"

    @property
    def context_name(self) -> str:
        """Get the context name of the message."""
        return self._context_name
    
    @property
    def message(self) -> str:
        """Get the message contents (a natural language string)."""
        return self._message

    @property
    def sender(self) -> str:
        """Get the sender of the message (or None if the sender was not specified)."""
        return self._sender
    @sender.setter
    def sender(self, sender: str):
        self._sender = sender
    
    @property
    def message_type(self) -> WiseAgentMessageType:
        """Get the type of the message (or None if the type was not specified)."""
        return self._message_type
    @property
    def identifier(self) -> int:
        """Get the id of the message."""
        return self._identifier

class WiseAgentTransport(ABC):
    
    def set_call_backs(self, request_receiver: Optional[Callable[[], WiseAgentMessage]] = None,
                 event_receiver: Optional[Callable[[], WiseAgentEvent]] = None,
                 error_receiver: Optional[Callable[[], WiseAgentMessage]] = None,
                 response_receiver: Optional[Callable[[], WiseAgentMessage]] = None):
        self._request_receiver = request_receiver
        self._event_receiver = event_receiver
        self._error_receiver = error_receiver
        self._response_receiver = response_receiver
        
    
    @abstractmethod
    def send_request(self, message: WiseAgentMessage, dest_agent_name: str):
        """
        Send a request message to an agent.

        Args:
            message (WiseAgentMessage): the message to send
        """
        pass
    
    @abstractmethod
    def send_response(self, message: WiseAgentMessage, dest_agent_name: str):
        """
        Send a request message to an agent.

        Args:
            message (WiseAgentMessage): the message to send
        """
        pass
    
    @abstractmethod
    def stop(self):
        """
        Stop the transport.
        """
        pass
    
    @property
    def request_receiver(self) -> Optional[Callable[[], WiseAgentMessage]]:
        """Get the message receiver callback."""
        return self._request_receiver
    
    @property
    def event_receiver(self) -> Optional[Callable[[], WiseAgentEvent]]:
        """Get the event receiver callback."""
        return self._event_receiver
    
    @property
    def error_receiver(self) -> Optional[Callable[[], WiseAgentMessage]]:
        """Get the error receiver callback."""
        return self._error_receiver
    
    @property
    def response_receiver(self) -> Optional[Callable[[], WiseAgentMessage]]:
        """Get the response receiver callback."""
        return self._response_receiver
    
    
    
