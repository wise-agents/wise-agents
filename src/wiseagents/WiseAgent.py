from abc import ABC, abstractmethod
from typing import Optional

from wiseagents.graphdb.WiseAgentGraphDB import WiseAgentGraphDB
from  wiseagents.llm.WiseAgentLLM import WiseAgentLLM

from wiseagents.WiseAgentEvent import WiseAgentEvent
from wiseagents.WiseAgentMessage import WiseAgentMessage
from wiseagents.vectordb.WiseAgentVectorDB import WiseAgentVectorDB
import yaml


class WiseAgent(yaml.YAMLObject):

    yaml_tag = u'!wiseagents.WiseAgent'
    def __init__(self, name: str, description: str, llm: Optional[WiseAgentLLM] = None,
                 vector_db: Optional[WiseAgentVectorDB] = None, graph_db: Optional[WiseAgentGraphDB] = None):
        self._name = name
        self._description = description
        self._llm = llm
        self._vector_db = vector_db
        self._graph_db = graph_db
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm}, vector_db={self.vector_db}, graph_db={self.graph_db})"
    
    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def description(self) -> str:
        """Get a description of what the agent does."""
        return self._description

    @property
    def llm(self) -> Optional[WiseAgentLLM]:
        """Get the LLM associated with the agent."""
        return self._llm

    @property
    def vector_db(self) -> Optional[WiseAgentVectorDB]:
        """Get the vector DB associated with the agent."""
        return self._vector_db
    
    @property
    def graph_db(self) -> Optional[WiseAgentGraphDB]:
        """Get the graph DB associated with the agent."""
        return self._graph_db

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

    @abstractmethod
    def receive_event(self) -> WiseAgentEvent:
        """
        Receive an event.

        Returns:
            WiseAgentEvent: the event that has been received
        """
        ...

    @abstractmethod
    def process_event(self, event: WiseAgentEvent) -> WiseAgentMessage:
        """
        Process the given event.

        Args:
            event (WiseAgentEvent): the event to be processed

        Returns:
            WiseAgentMessage: the message to send to another agent
        """
        ...
