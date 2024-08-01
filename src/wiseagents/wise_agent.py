from abc import ABC, abstractmethod
import json
import logging
from typing import Callable, Optional

from wiseagents.graphdb import WiseAgentGraphDB
from wiseagents.llm.openai_API_wise_agent_LLM import OpenaiAPIWiseAgentLLM
from wiseagents.llm.wise_agent_LLM import WiseAgentLLM

from wiseagents.wise_agent_messaging import WiseAgentMessage, WiseAgentTransport, WiseAgentEvent
from wiseagents.vectordb import WiseAgentVectorDB
import yaml
from openai.types.chat import ChatCompletionToolParam


class WiseAgent(yaml.YAMLObject):

    yaml_tag = u'!wiseagents.WiseAgent'
    def __init__(self, name: str, description: str, transport: WiseAgentTransport, llm: Optional[WiseAgentLLM] = None,
                 vector_db: Optional[WiseAgentVectorDB] = None, collection_name: Optional[str] = "wise-agent-collection",
                 graph_db: Optional[WiseAgentGraphDB] = None):
        self._name = name
        self._description = description
        self._llm = llm
        self._vector_db = vector_db
        self._collection_name = collection_name
        self._graph_db = graph_db
        self._transport = transport
        self.startAgent()
        
    def startAgent(self):
        self.transport.set_call_backs(self.process_request, self.process_event, self.process_error, self.process_response)
        self.transport.start()
        WiseAgentRegistry.register_agent(self) 
    def stopAgent(self):
        self.transport.stop()
        WiseAgentRegistry.remove_agent(self.name)
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self._collection_name}, graph_db={self.graph_db})")
    
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
    def collection_name(self) -> str:
        """Get the vector DB collection name associated with the agent."""
        return self._collection_name

    @property
    def graph_db(self) -> Optional[WiseAgentGraphDB]:
        """Get the graph DB associated with the agent."""
        return self._graph_db
    
    @property
    def transport(self) -> WiseAgentTransport:
        """Get the transport associated with the agent."""
        return self._transport
    
    def send_request(self, message: WiseAgentMessage, dest_agent_name: str):
        message.sender = self.name
        context = WiseAgentRegistry.get_or_create_context(message.context_name)
        context.add_participant(self)
        self.transport.send_request(message, dest_agent_name)
        context.message_trace.append(message)
    
    def send_response(self, message: WiseAgentMessage, dest_agent_name):
        message.sender = self.name
        context = WiseAgentRegistry.get_or_create_context(message.context_name)
        context.add_participant(self)
        self.transport.send_response(message, dest_agent_name)
        context.message_trace.append(message)  
    
    @abstractmethod
    def process_request(self, message: WiseAgentMessage) -> bool:
        """
        Callback method to process the given request for this agent.

        Args:
            message (WiseAgentMessage): the message to be processed

        Returns:
            True if the message was processed successfully, False otherwise
        """
        ...

    @abstractmethod
    def process_response(self, message: WiseAgentMessage) -> bool:
        """
        Callback method to process the response received from another agent which processed a request from this agent.

        Args:
            message (WiseAgentMessage): the message to be processed

        Returns:
            True if the message was processed successfully, False otherwise
        """
        ...

    @abstractmethod
    def process_event(self, event: WiseAgentEvent) -> bool:
        """
        Callback method to process the given event.

        Args:
            event (WiseAgentEvent): the event to be processed

        Returns:
           True if the event was processed successfully, False otherwise
        """
        ...
        
    @abstractmethod
    def process_error(self, error: Exception) -> bool:
        """
        Callback method to process the given error.

        Args:
            error (Exception): the error to be processed

        Returns:
            True if the error was processed successfully, False otherwise
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

class WiseAgentTool(yaml.YAMLObject):
    yaml_tag = u'!wiseagents.WiseAgentTool'
    def __init__(self, name: str, description: str, parameters_json_schema: dict = {}, call_back : Optional[Callable[...,str]] = None):    
       self._name = name
       self._description = description
       self._parameters_json_schema = parameters_json_schema
       
       if call_back is None:
           self._call_back = self.default_call_back
       else:
           self._call_back = call_back
       WiseAgentRegistry.register_tool(self)
   
    @classmethod
    def from_yaml(cls, loader, node):
        data = loader.construct_mapping(node, deep=True)
        return cls(name=data.get('_name'), description=data.get('_description'), 
                   parameters_json_schema=data.get('_parameters_json_schema'),
                   call_back=data.get('_call_back'))
    
    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return self._name
    
    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return self._description
    
    @property
    def call_back(self) -> Callable[...,str]:
        """Get the callback function of the tool."""
        return self._call_back
    @property
    def json_schema(self) -> dict:
        """Get the json schema of the tool."""
        return self._parameters_json_schema
       
    def get_tool_OpenAI_format(self) -> ChatCompletionToolParam:
        '''The tool should be able to return itself in the form of a ChatCompletionToolParam'''
        return {"type": "function",
                "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.json_schema
                } 
        }
    
    def gefault_call_back(self, **kwargs) -> str:
        '''The tool should be able to execute the function with the given parameters'''
        return json.dumps(kwargs)
    
    def exec(self, **kwargs) -> str:
        '''The tool should be able to execute the function with the given parameters'''
        return self.call_back(**kwargs)



class WiseAgentContext():
    from typing import List
    
    _message_trace : List[WiseAgentMessage] = []
    _participants : List[WiseAgent] = []
    
    def __init__(self, name: str):
        self._name = name
        WiseAgentRegistry.register_context(self)
        
    @property
    def name(self) -> str:
        """Get the name of the context."""
        return self._name
    
    @property
    def message_trace(self) -> List[WiseAgentMessage]:
        """Get the message trace of the context."""
        return self._message_trace
    @property
    def participants(self) -> List[WiseAgent]:
        """Get the participants of the context."""
        return self._participants
    
    def add_participant(self, agent: WiseAgent):
        if agent not in self._participants:
            self._participants.append(agent) 
        
class WiseAgentRegistry:

    """
    A Registry to get available agents and running contexts
    """
    agents : dict[str, WiseAgent] = {}
    contexts : dict[str, WiseAgentContext] = {}
    tools: dict[str, WiseAgentTool] = {}
    
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
    def does_context_exist(cls, context_name: str) -> bool:
        """
        Get the context with the given name
        """
        if  cls.contexts.get(context_name) is None:
            return False
        else:
            return True
    
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
        
    @classmethod
    def register_tool(cls, tool : WiseAgentTool):
        """
        Register a tool with the registry
        """
        cls.tools[tool.name] = tool
    
    @classmethod
    def get_tools(cls) -> dict[str, WiseAgentTool]:
        """
        Get the list of tools
        """
        return cls.tools
    
    @classmethod
    def get_tool(cls, tool_name: str) -> WiseAgentTool:
        """
        Get the tool with the given name
        """
        return cls.tools.get(tool_name)
        
        
