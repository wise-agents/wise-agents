from abc import ABC, abstractmethod
import json
import logging
from typing import Any, Callable, Dict, Iterable, Optional
from uuid import UUID

from wiseagents.graphdb import WiseAgentGraphDB
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.llm import WiseAgentLLM

from wiseagents.wise_agent_messaging import WiseAgentMessage, WiseAgentTransport, WiseAgentEvent
from wiseagents.vectordb import WiseAgentVectorDB
import yaml
from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessageParam


class WiseAgent(yaml.YAMLObject):
    ''' A WiseAgent is an abstract class that represents an agent that can send and receive messages to and from other agents.
    '''
    yaml_tag = u'!wiseagents.WiseAgent'
    def __init__(self, name: str, description: str, transport: WiseAgentTransport, llm: Optional[WiseAgentLLM] = None,
                 vector_db: Optional[WiseAgentVectorDB] = None, collection_name: Optional[str] = "wise-agent-collection",
                 graph_db: Optional[WiseAgentGraphDB] = None):
        ''' 
        Initialize the agent with the given name, description, transport, LLM, vector DB, collection name, and graph DB.
        

        Args:
            name (str): the name of the agent
            description (str): a description of what the agent does
            transport (WiseAgentTransport): the transport to use for sending and receiving messages
            llm Optional(WiseAgentLLM): the LLM associated with the agent
            vector_db Optional(WiseAgentVectorDB): the vector DB associated with the agent
            collection_name Optional(str) = "wise-agent-collection": the vector DB collection name associated with the agent
            graph_db Optional (WiseAgentGraphDB): the graph DB associated with the agent 
        '''
        self._name = name
        self._description = description
        self._llm = llm
        self._vector_db = vector_db
        self._collection_name = collection_name
        self._graph_db = graph_db
        self._transport = transport
        self.startAgent()
        
    def startAgent(self):
        ''' Start the agent by setting the call backs and starting the transport.'''
        self.transport.set_call_backs(self.process_request, self.process_event, self.process_error, self.process_response)
        self.transport.start()
        WiseAgentRegistry.register_agent(self) 
    def stopAgent(self):
        ''' Stop the agent by stopping the transport and removing the agent from the registry.'''
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
        '''Send a request message to the destination agent with the given name.

        Args:
            message (WiseAgentMessage): the message to send
            dest_agent_name (str): the name of the destination agent'''
        message.sender = self.name
        context = WiseAgentRegistry.get_or_create_context(message.context_name)
        context.add_participant(self)
        self.transport.send_request(message, dest_agent_name)
        context.message_trace.append(message)
    
    def send_response(self, message: WiseAgentMessage, dest_agent_name):
        '''Send a response message to the destination agent with the given name.

        Args:
            message (WiseAgentMessage): the message to send
            dest_agent_name (str): the name of the destination agent'''
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
    ''' A WiseAgentTool is an abstract class that represents a tool that can be used by an agent to perform a specific task.'''
    yaml_tag = u'!wiseagents.WiseAgentTool'
    def __init__(self, name: str, description: str, agent_tool: bool, parameters_json_schema: dict = {}, 
                 call_back : Optional[Callable[...,str]] = None):
       ''' Initialize the tool with the given name, description, agent tool, parameters json schema, and call back.

       Args:
           name (str): the name of the tool
           description (str): a description of what the tool does
           agent_tool (bool): whether the tool is an agent tool
           parameters_json_schema (dict): the json schema for the parameters of the tool
           call_back Optional(Callable[...,str]): the callback function to execute the tool'''     
       self._name = name
       self._description = description
       self._parameters_json_schema = parameters_json_schema
       self._agent_tool = agent_tool
       self._call_back = call_back
       WiseAgentRegistry.register_tool(self)
   
    @classmethod
    def from_yaml(cls, loader, node):
        '''Load the tool from a YAML node.

        Args:
            loader (yaml.Loader): the YAML loader
            node (yaml.Node): the YAML node'''
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
    
    @property
    def is_agent_tool(self) -> bool:
        """Get the agent tool of the tool."""
        return self._agent_tool
       
    def get_tool_OpenAI_format(self) -> ChatCompletionToolParam:
        '''The tool should be able to return itself in the form of a ChatCompletionToolParam
        
        Returns:
            ChatCompletionToolParam'''
        return {"type": "function",
                "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.json_schema
                } 
        }
    
    def default_call_back(self, **kwargs) -> str:
        '''The tool should be able to execute the function with the given parameters'''
        return json.dumps(kwargs)
    
    def exec(self, **kwargs) -> str:
        '''The tool should be able to execute the function with the given parameters'''
        if self.call_back is None:
            return self.default_call_back(**kwargs)
        return self.call_back(**kwargs)



class WiseAgentContext():
    from typing import List
    ''' A WiseAgentContext is a class that represents a context in which agents can communicate with each other.
    '''
    
    _message_trace : List[WiseAgentMessage] = []
    _participants : List[WiseAgent] = []
    _llm_chat_completion : Dict[str, List[ChatCompletionMessageParam]] = {}
    _llm_required_tool_call : Dict[str, List[str]] = {}
    _llm_available_tools_in_chat : Dict[str, List[ChatCompletionToolParam]] = {}
    _agents_sequence : List[str] = []
    
    
    def __init__(self, name: str):
        ''' Initialize the context with the given name.

        Args:
            name (str): the name of the context'''
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
    
    @property
    def llm_chat_completion(self) -> Dict[str, List[ChatCompletionMessageParam]]:
        """Get the LLM chat completion of the context."""
        return self._llm_chat_completion
    
    def add_participant(self, agent: WiseAgent):
        '''Add a participant to the context.

        Args:
            agent (WiseAgent): the agent to add'''
            
        if agent not in self._participants:
            self._participants.append(agent)
    
    def append_chat_completion(self, chat_uuid: str, messages: Iterable[ChatCompletionMessageParam]):
        '''Append chat completion to the context.

        Args:
            chat_uuid (str): the chat uuid
            messages (Iterable[ChatCompletionMessageParam]): the messages to append'''
            
        if chat_uuid not in self._llm_chat_completion:
            self._llm_chat_completion[chat_uuid] = []
        self._llm_chat_completion[chat_uuid].append(messages)
    
    @property
    def llm_required_tool_call(self) -> Dict[str, List[str]]:
        """Get the LLM required tool call of the context.
        return Dict[str, List[str]]"""
        return self._llm_required_tool_call
    
    def append_required_tool_call(self, chat_uuid: str, tool_name: str):
        '''Append required tool call to the context.

        Args:
            chat_uuid (str): the chat uuid
            tool_name (str): the tool name to append'''
        if chat_uuid not in self._llm_required_tool_call:
            self._llm_required_tool_call[chat_uuid] = []
        self._llm_required_tool_call[chat_uuid].append(tool_name)
    
    def remove_required_tool_call(self, chat_uuid: str, tool_name: str):
        '''Remove required tool call from the context.

        Args:
            chat_uuid (str): the chat uuid
            tool_name (str): the tool name to remove'''
        if chat_uuid in self._llm_required_tool_call:
            self._llm_required_tool_call[chat_uuid].remove(tool_name)
            if len(self._llm_required_tool_call[chat_uuid]) == 0:
                self._llm_required_tool_call.pop(chat_uuid)
                
    def get_required_tool_calls(self, chat_uuid: str) -> List[str]:
        '''Get required tool calls from the context.

        Args:
            chat_uuid (str): the chat uuid
            return List[str]'''
        if chat_uuid in self._llm_required_tool_call:
            return self._llm_required_tool_call[chat_uuid]
        else:
            return []   
        
    @property
    def llm_available_tools_in_chat(self) -> Dict[str, List[ChatCompletionToolParam]]:
        """Get the LLM available tools in chat of the context."""
        return self._llm_available_tools_in_chat
    
    def append_available_tool_in_chat(self, chat_uuid: str, tools: Iterable[ChatCompletionToolParam]):
        '''Append available tool in chat to the context.

        Args:
            chat_uuid (str): the chat uuid
            tools (Iterable[ChatCompletionToolParam]): the tools to append'''
        if chat_uuid not in self._llm_available_tools_in_chat:
            self._llm_available_tools_in_chat[chat_uuid] = []
        self._llm_available_tools_in_chat[chat_uuid].append(tools)
    
    def get_available_tools_in_chat(self, chat_uuid: str) -> List[ChatCompletionToolParam]:
        '''Get available tools in chat from the context.

        Args:
            chat_uuid (str): the chat uuid
            return List[ChatCompletionToolParam]'''
        if chat_uuid in self._llm_available_tools_in_chat:
            return self._llm_available_tools_in_chat[chat_uuid]
        else:
            return []

    @property
    def agents_sequence(self) -> List[str]:
        """
        Get the sequence of agents for this context.

        Returns:
            List[str]: the sequence of agents or an empty list if no sequence has been set
        """
        return self._agents_sequence

    def set_agents_sequence(self, agents_sequence: List[str]):
        """
        Set the sequence of agents for this context.


        Args:
            agents_sequence (List[str]): the sequence of agents
        """
        self._agents_sequence = agents_sequence

    def get_next_agent_in_sequence(self, current_agent: str):
        """
        Get the next agent in the sequence of agents for this context.


        Args:
            current_agent (str): the name of the current agent

        Returns:
            str: the name of the next agent in the sequence after the current agent or None if there are no remaining
            agents in the sequence after the current agent
        """
        if current_agent in self._agents_sequence:
            current_agent_index = self._agents_sequence.index(current_agent)
            next_agent_index = current_agent_index + 1
            if next_agent_index < len(self._agents_sequence):
                return self._agents_sequence[next_agent_index]
        return None

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
        
        
