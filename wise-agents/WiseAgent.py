from abc import ABC, abstractmethod
from typing import Optional

import WiseAgentLLM
import WiseAgentMessage


class WiseAgent(ABC):

    def __init__(self, name: str, description: str, llm: Optional[WiseAgentLLM] = None):
        self._name = name
        self._description = description
        self._llm = llm

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def description(self) -> str:
        """Get a description of what the agent does."""
        return self._description

    @abstractmethod
    def receive_message(self) -> WiseAgentMessage:
        """
        Receive a message.

        Returns:
            WiseAgentMessage: the message that has been received
        """
        ...

    @abstractmethod
    def process_message(self, message: WiseAgentMessage) -> WiseAgentMessage:
        """
        Process the given message.

        Args:
            message (WiseAgentMessage): the message to be processed

        Returns:
            WiseAgentMessage or None: the message to send to another agent or None
            if no further messages are needed
        """
        ...

    @abstractmethod
    def get_recipient_agent_name(self, message: WiseAgentMessage) -> str:
        """
        Get the name of the agent to send the given message to.

        Args:
             message (WiseAgentMessage): the message to be sent

        Returns:
            str: the name of the agent to send the given message to
        """
        ...

    @abstractmethod
    def send_message(self, message: WiseAgentMessage, agent_name: str) -> bool:
        """
        Send the given message to the specified agent.

        Args:
            message (WiseAgentMessage): the message to be sent
            agent_name (str): the name of the agent to send the message to

        Returns:
            bool: True if the message was sent successfully and False otherwise
        """
        ...


