from abc import ABC, abstractmethod
from typing import Optional

from wiseagents.graphdb import WiseAgentGraphDB
from  wiseagents.llm.wise_agent_LLM import WiseAgentLLM

from wiseagents.wise_agent_event import WiseAgentEvent
from wiseagents.wise_agent_message import WiseAgentMessage
from wiseagents.vectordb.wise_agent_vectorDB import WiseAgentVectorDB
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
        WiseAgentRegistry.register_agent(self) 
    
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


class WiseAgentContext():
    message_trace : [WiseAgentMessage] = []
    participants : [WiseAgent] = []
    
    def __init__(self, name: str):
        self._name = name
        WiseAgentRegistry.register_context(self)
        
    @property
    def name(self) -> str:
        """Get the name of the context."""
        return self._name
    
    @property
    def message_trace(self) -> [WiseAgentMessage]:
        """Get the message trace of the context."""
        return self.message_trace
        
class WiseAgentRegistry:

    """
    A Registry to get available agents and running contexts
    """
    agents : dict[str, WiseAgent] = {}
    contexts : dict[str, WiseAgentContext] = {}
    
    @classmethod
    def register_agent(cls,agent : WiseAgent):
        """
        Register an agent with the registry
        """
        cls.agents[agent.name] = agent
    @classmethod    
    def register_context(cls, context : WiseAgentContext):
        """
        Register a context with the registry
        """
        cls.contexts[context.name] = context
    @classmethod    
    def get_agents(cls) -> dict [str, WiseAgent]:
        """
        Get the list of agents
        """
        return cls.agents
    
    @classmethod
    def get_contexts(cls) -> dict [str, WiseAgentContext]:
        """
        Get the list of contexts
        """
        return cls.contexts
    
    @classmethod
    def get_agent(cls, agent_name: str) -> WiseAgent:
        """
        Get the agent with the given name
        """
        return cls.agents.get(agent_name) 
    
    @classmethod
    def get_or_create_context(cls, context_name: str) -> WiseAgentContext:
        """ Get the context with the given name """
        context = cls.contexts.get(context_name)
        if context is None:
            return WiseAgentContext(context_name)
        else:
            return context
        
    @classmethod
    def get_context(cls, context_name: str) -> WiseAgentContext:
        """
        Get the context with the given name
        """
        return cls.contexts.get(context_name)
    
    @classmethod
    def remove_agent(cls, agent_name: str):
        """
        Remove the agent from the registry
        """
        cls.agents.pop(agent_name)
        
    @classmethod
    def remove_context(cls, context_name: str):
        """
        Remove the context from the registry
        """
        cls.contexts.pop(context_name)
    
    @classmethod
    def clear_agents(cls):
        """
        Clear all agents from the registry
        """
        cls.agents.clear()
    
    @classmethod
    def clear_contexts(cls):
        """
        Clear all contexts from the registry
        """
        cls.contexts.clear()
        
        
