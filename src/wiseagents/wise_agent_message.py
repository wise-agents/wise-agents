from typing import Optional

from wiseagents.wise_agent_message_type import WiseAgentMessageType


class WiseAgentMessage:
    def __init__(self, message: str, sender: Optional[str] = None, message_type: Optional[WiseAgentMessageType] = None):
        self._message = message
        self._sender = sender
        self._message_type = message_type

    @property
    def message(self) -> str:
        """Get the message contents (a natural language string)."""
        return self._message

    @property
    def sender(self) -> str:
        """Get the sender of the message (or None if the sender was not specified)."""
        return self._sender

    @property
    def message_type(self) -> WiseAgentMessageType:
        """Get the type of the message (or None if the type was not specified)."""
        return self._message_type


class WiseAgentMessageWithTracing(WiseAgentMessage):
    def __init__(self, message: str, sender: Optional[str] = None,
                 message_type: Optional[WiseAgentMessageType] = None, trace: Optional[WiseAgentMessage] = []):
        super().__init__(message, sender, message_type)
        self._trace = trace.append(self)

    @property
    def trace(self) -> str:
        """Get the trace of the message (or None if the trace was not specified)."""
        return self._trace
