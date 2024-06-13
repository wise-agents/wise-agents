from typing import Optional

import WiseAgentMessageType


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



