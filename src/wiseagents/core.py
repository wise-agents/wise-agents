import copy
import json
import logging
import os
import pickle

from abc import abstractmethod
from enum import StrEnum, auto
from typing import Any, Callable, Dict, Iterable, List, Optional

import yaml
from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessageParam

import redis

from wiseagents import enforce_no_abstract_class_instances
from wiseagents.graphdb import WiseAgentGraphDB
from wiseagents.llm import OpenaiAPIWiseAgentLLM, WiseAgentLLM
from wiseagents.yaml import WiseAgentsYAMLObject
from wiseagents.vectordb import WiseAgentVectorDB
from wiseagents.wise_agent_messaging import WiseAgentMessage, WiseAgentMessageType, WiseAgentTransport, WiseAgentEvent


class WiseAgentCollaborationType(StrEnum):
    SEQUENTIAL = auto()
    SEQUENTIAL_MEMORY = auto()
    PHASED = auto()
    INDEPENDENT = auto()
    CHAT = auto()


class WiseAgentTool(WiseAgentsYAMLObject):
    ''' WiseAgentTool represents a tool that can be used by an agent to perform a specific task.'''
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
    
    ''' A WiseAgentContext is a class that represents a context in which agents can communicate with each other.
    '''
    
    _message_trace : List[str] = []
    
    # A list of chat completion messages
    _llm_chat_completion : List[ChatCompletionMessageParam] = []
    
    # A list of tool names that need to be executed
    _llm_required_tool_call : List[str] = []
    
    # A list of available tools in chat
    _llm_available_tools_in_chat : List[ChatCompletionToolParam] = []

    # A list of agent names that need to be executed in sequence
    # Used by a sequential coordinator
    _agents_sequence : List[str] = []

    # The agent where the final response should be routed to
    # Used by both a sequential coordinator and a phased coordinator
    _route_response_to : str = None

    # A list that contains a list of agent names to be executed for each phase
    # Used by a phased coordinator
    _agent_phase_assignments : List[List[str]] = []

    # Maps a chat uuid to the current phase. Used by a phased coordinator.
    _current_phase :  int = None

    # A list of agent names that need to be executed for the current phase
    # Used by a phased coordinator
    _required_agents_for_current_phase : List[str] = []

    # A list containing the queries attempted for each iteration executed by
    # the phased coordinator or sequential memory coordinator
    _queries : List[str] = []

    # The collaboration type
    _collaboration_type: WiseAgentCollaborationType = None

    # A boolean value indicating whether to restart a sequence of agents
    _restart_sequence: bool = False

    _redis_db : redis.Redis = None
    _use_redis : bool = False
    _config : Dict[str, Any] = {}
    _trace_enabled : bool = False


    def __init__(self, name: str, config : Optional[Dict[str,Any]] = {"use_redis": False}):
        ''' Initialize the context with the given name.

        Args:
            name (str): the name of the context'''
        self._name = name
        self._config = config
        WiseAgentRegistry.register_context(self)
        if config.get("use_redis") == True and self._redis_db is None:
            self._redis_db = redis.Redis(host=self._config["redis_host"], port=self._config["redis_port"])
            self._use_redis = True
        if (config.get("trace_enabled") == True):
            self._trace_enabled = True
        
    
    def __repr__(self) -> str:
        '''Return a string representation of the context.'''
        return (f"{self.__class__.__name__}(name={self.name}, message_trace={self.message_trace},"
                f"llm_chat_completion={self.llm_chat_completion}, collaboration_type={self.collaboration_type},"
                f"llm_required_tool_call={self.llm_required_tool_call}, llm_available_tools_in_chat={self.llm_available_tools_in_chat},"
                f"agents_sequence={self._agents_sequence}, route_response_to={self._route_response_to},"
                f"agent_phase_assignments={self._agent_phase_assignments}, current_phase={self._current_phase},"
                f"required_agents_for_current_phase={self._required_agents_for_current_phase}, queries={self._queries})")
    def __eq__(self, value: object) -> bool:
        return isinstance(value, WiseAgentContext) and self.__repr__() == value.__repr__()
    
    def __getstate__(self) -> object:
        '''Get the state of the context.'''
        state = super().__getstate__()
        if '_redis_db' in state:
            del state['_redis_db']
            del state['_use_redis']
        return state
    
    def __setstate__(self, state: object):
        '''Set the state of the context.'''
        self.__dict__.update(state)
        if self._config.get("use_redis") == True and self._redis_db is None:
            self._redis_db = redis.Redis(host=self._config["redis_host"], port=self._config["redis_port"])
            self._use_redis = True

    def _append_to_redis_list(self, key: str, value: Any):
        '''Append a value to a list in redis.'''
        pipe = self._redis_db.pipeline(transaction=True)
        while True:
            pipe.watch(self.name)
            try:
                if(pipe.hexists(self.name, key) == False):
                    pipe.multi()
                    pipe.hset(self.name, key, value=pickle.dumps([value]))
                    pipe.execute()
                    return
                else:
                    redis_stored_messages = pipe.hget(self.name, key)
                    stored_messages : List  = pickle.loads(redis_stored_messages)
                    stored_messages.append(value)
                    pipe.multi()
                    pipe.hset(self.name, key, value=pickle.dumps(stored_messages))
                    pipe.execute()
                    return
            except redis.WatchError:
                logging.debug("WatchError in append_to_redis_list for {key}")
                continue
    def _remove_from_redis_list(self, key: str, value: Any):
        '''Remove a value to a list in redis.'''
        pipe = self._redis_db.pipeline(transaction=True)
        while True:
            pipe.watch(self.name)
            try:
                if(pipe.hexists(self.name, key) == False):
                    pipe.unwatch()
                    return
                else:
                    redis_stored_messages = pipe.hget(self.name, key)
                    stored_messages : List  = pickle.loads(redis_stored_messages)
                    stored_messages.remove(value)
                    pipe.multi()
                    pipe.hset(self.name, key, value=pickle.dumps(stored_messages))
                    pipe.execute()
                    return
            except redis.WatchError:
                logging.debug("WatchError in remove_from_redis_list for {key}")
                continue

    def _get_list_from_redis(self, key: str) -> List:
        '''Get a list from redis.'''
        redis_return =  self._redis_db.hget(self.name, key)
        if (redis_return is not None):
            return pickle.loads(redis_return)
        else:
            return []

    @property   
    def name(self) -> str:
        """Get the name of the context."""
        return self._name
    
    @property
    def trace_enabled(self) -> bool:
        """Get the trace enabled of the context."""
        return self._trace_enabled

    @property
    def message_trace(self) -> List[str]:
        """Get the message trace of the context."""
        if (self._use_redis == True):
            return self._get_list_from_redis("message_trace")
        else:
            return self._message_trace

    def trace(self, message : WiseAgentMessage):
        '''Trace the message.'''
        if (self.trace_enabled):
            if (self._use_redis == True):
                self._append_to_redis_list("message_trace", message.__repr__())
            else:
                self._message_trace.append(message)   
                
    
    @property
    def llm_chat_completion(self) -> List[ChatCompletionMessageParam]:
        """Get the LLM chat completion of the context."""
        if (self._use_redis == True):
            return self._get_list_from_redis("llm_chat_completion")
        else:
            return self._llm_chat_completion   
            
    
    def append_chat_completion(self, messages: Iterable[ChatCompletionMessageParam]):
        '''Append chat completion to the context.

        Args:
            messages (Iterable[ChatCompletionMessageParam]): the messages to append'''
            
        if (self._use_redis == True):
            self._append_to_redis_list("llm_chat_completion", messages)
        else:
            self._llm_chat_completion.append(messages)


    @property
    def llm_required_tool_call(self) -> List[str]:
        """Get the LLM required tool call of the context.
        return List[str]"""
        if (self._use_redis == True):
            return self._get_list_from_redis("llm_required_tool_call")
        else:
            return self._llm_required_tool_call
    
    def append_required_tool_call(self, tool_name: str):
        '''Append required tool call to the context.

        Args:
            tool_name (str): the tool name to append'''
        if (self._use_redis == True):
            self._append_to_redis_list("llm_required_tool_call", tool_name)
        else:
            self._llm_required_tool_call.append(tool_name)
    
    def remove_required_tool_call(self, tool_name: str):
        '''Remove required tool call from the context.

        Args:
            tool_name (str): the tool name to remove'''
        if (self._use_redis == True):
            self._remove_from_redis_list("llm_required_tool_call", tool_name) #remove first occurence of tool_name
        else:
            self._llm_required_tool_call.remove(tool_name) #remove first occurence of tool_name
        
    @property
    def llm_available_tools_in_chat(self) -> List[ChatCompletionToolParam]:
        """Get the LLM available tools in chat of the context."""
        if (self._use_redis == True):
            return self._get_list_from_redis("llm_available_tools_in_chat")
        else:
            return self._llm_available_tools_in_chat
    
    def append_available_tool_in_chat(self, tools: Iterable[ChatCompletionToolParam]):
        '''Append available tool in chat to the context.

        Args:
            tools (Iterable[ChatCompletionToolParam]): the tools to append'''
        if (self._use_redis == True):
            self._append_to_redis_list("llm_available_tools_in_chat", tools)
        else:
            self._llm_available_tools_in_chat.append(tools)
    
    def get_agents_sequence(self) -> List[str]:
        """
        Get the sequence of agents for this context. This is used by a sequential
        coordinator to execute its agents in a specific order, passing the output from one agent in the sequence
        to the next agent in the sequence.

        
        Returns:
            List[str]: the sequence of agents names or an empty list if no sequence has been set for this context
        """
        if (self._use_redis == True):
            return self._get_list_from_redis("agents_sequence")
        else:
            return self._agents_sequence

    def set_agents_sequence(self, agents_sequence: List[str]):
        """
        Set the sequence of agents for this context. This is used by
        a sequential coordinator to execute its agents in a specific order, passing the output
        from one agent in the sequence to the next agent in the sequence.

        Args:
            agents_sequence (List[str]): the sequence of agent names
        """
        if (self._use_redis == True):
            self._redis_db.hset(self.name, "agents_sequence", pickle.dumps(agents_sequence))
        else:
            self._agents_sequence = agents_sequence

    def get_route_response_to(self) -> Optional[str]:
        """
        Get the name of the agent where the final response should be routed to for this
        context. This is used by a sequential coordinator and a phased coordinator.

        Returns:
            Optional[str]: the name of the agent where the final response should be routed to or None if no agent is set
        """
        if (self._use_redis == True):
            return self._redis_db.hget(self.name, "route_response_to").decode("utf-8")
        else: 
            return self._route_response_to
            
    def set_route_response_to(self, agent: str):
        """
        Set the name of the agent where the final response should be routed to for this
        context. This is used by a sequential coordinator and a phased coordinator.

        Args:
            agent (str): the name of the agent where the final response should be routed to
        """
        if (self._use_redis == True):
            self._redis_db.hset(self.name, "route_response_to", agent)
        else:
            self._route_response_to = agent

    def get_next_agent_in_sequence(self, current_agent: str):
        """
        Get the name of the next agent in the sequence of agents for this context.
        This is used by a sequential coordinator to determine the name of the next agent to execute.

        Args:
            current_agent (str): the name of the current agent

        Returns:
            str: the name of the next agent in the sequence after the current agent or None if there are no remaining
            agents in the sequence after the current agent
        """
        agents_sequence = self.get_agents_sequence()
        if current_agent in agents_sequence:
            current_agent_index = agents_sequence.index(current_agent)
            next_agent_index = current_agent_index + 1
            if next_agent_index < len(agents_sequence):
                return agents_sequence[next_agent_index]
        return None

    def get_agent_phase_assignments(self) -> List[List[str]]:
        """
        Get the agents to be executed in each phase for this context. This is used
        by a phased coordinator.

        Args:
            
        Returns:
            List[List[str]]: The agents to be executed in each phase, represented as a list of lists, where the
            size of the outer list corresponds to the number of phases and each element in the list is a list of
            agent names for that phase. An empty list is returned if no phases have been set for the
            given chat uuid
        """
        if (self._use_redis == True):
            return self._get_list_from_redis("agent_phase_assignments")
        else:
            return self._agent_phase_assignments


    def set_agent_phase_assignments(self, agent_phase_assignments: List[List[str]]):
        """
        Set the agents to be executed in each phase for this context. This is used
        by a phased coordinator.

        Args:
            agent_phase_assignments (List[List[str]]): The agents to be executed in each phase, represented as a
            list of lists, where the size of the outer list corresponds to the number of phases and each element
            in the list is a list of agent names for that phase.
        """
        if (self._use_redis == True):
            self._redis_db.hset(self.name, "agent_phase_assignments", value=pickle.dumps(agent_phase_assignments))
        else:
            self._agent_phase_assignments = agent_phase_assignments

    def get_current_phase(self) -> int:
        """
        Get the current phase for the given chat uuid for this context. This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid

        Returns:
            int: the current phase, represented as an integer in the zero-indexed list of phases
        """
        if (self._use_redis == True):
            redis_return = self._redis_db.hget(self.name, "current_phase")
            if redis_return is not None:
                return pickle.loads(redis_return)
            else:
                return None
        else:
            return self._current_phase

    def set_current_phase(self, phase: int):
        """
        Set the current phase for this context. This method also
        sets the required agents for the current phase. This is used by a phased coordinator.

        Args:
            phase (int): the current phase, represented as an integer in the zero-indexed list of phases
        """
        if (self._use_redis == True):
            pipeline=self._redis_db.pipeline(transaction=True)
            pipeline.hset(self.name, "current_phase", pickle.dumps(phase))
            pipeline.hset(self.name, "required_agents_for_current_phase", value=pickle.dumps(self.get_agent_phase_assignments()[phase]))
            pipeline.execute()
        else:
            self._current_phase = phase
            self._required_agents_for_current_phase = copy.deepcopy(self._agent_phase_assignments[phase])

    def get_agents_for_next_phase(self) -> Optional[List]:
        """
        Get the list of agents to be executed for the next phase for this context.
        This is used by a phased coordinator.

        Args:
    
        Returns:
            Optional[List[str]]: the list of agent names for the next phase or None if there are no more phases
        """
        current_phase = self.get_current_phase()
        next_phase = current_phase + 1
        if next_phase < len(self.get_agent_phase_assignments()):
            self.set_current_phase(next_phase)
            return self.get_agent_phase_assignments()[next_phase]
        return None

    def get_required_agents_for_current_phase(self) -> List[str]:
        """
        Get the list of agents that still need to be executed for the current phase for this
        context. This is used by a phased coordinator.

        Args:
            
        Returns:
            List[str]: the list of agent names that still need to be executed for the current phase or an empty list
            if there are no remaining agents that need to be executed for the current phase
        """
        if (self._use_redis == True):
            return self._get_list_from_redis("required_agents_for_current_phase")
        else:
            return self._required_agents_for_current_phase

    def remove_required_agent_for_current_phase(self, agent_name: str):
        """
        Remove the given agent from the list of required agents for the current phase for this
        context. This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid
            agent_name (str): the name of the agent to remove
        """
        if (self._use_redis == True):
            self._remove_from_redis_list("required_agents_for_current_phase", agent_name)
        else:
            self._required_agents_for_current_phase.remove(agent_name)

    def get_current_query(self) -> Optional[str]:
        """
        Get the current query for the given chat uuid for this context. This is used by a phased coordinator.
        Can also be used for sequential memory coordination.

        Args:
            
        Returns:
            Optional[str]: the current query or None if there is no current query
        """
        if (self._use_redis == True):
            return self._get_list_from_redis("queries")[0]
        else:
            if self._queries:
                # return the last query
                return self._queries[-1]
            else:
                return None

    def add_query(self, query: str):
        """
        Add the current query for this context. This is used by a phased coordinator.
        Can also be used for sequential memory coordination.

        Args:
            query (str): the current query
        """
        if (self._use_redis == True):
            self._append_to_redis_list("queries", query)
        else:
            self._queries.append(query)

    def get_queries(self) -> List[str]:
        """
        Get the queries attempted for this context. This is used by a phased coordinator.
        Can also be used for sequential memory coordination.

        Returns:
            List[str]: the queries attempted for the given chat uuid for this context
        """
        if (self._use_redis == True):
            return self._get_list_from_redis("queries")
        else:
            return self._queries
        
    @property
    def collaboration_type(self) -> WiseAgentCollaborationType:
        """Get the collaboration type for this context."""
        if (self._use_redis == True):
            collaboration_type = self._redis_db.hget(self.name, "collaboration_type")
            if (collaboration_type is not None):
                return WiseAgentCollaborationType(collaboration_type.decode("utf-8"))
            else:
                return WiseAgentCollaborationType.INDEPENDENT   
        else:
            return self._collaboration_type

    def set_collaboration_type(self, collaboration_type: WiseAgentCollaborationType):
        """
        Set the collaboration type for this context.

        Args:
            collaboration_type (WiseAgentCollaborationType): the collaboration type
        """
            
        if (self._use_redis == True):
            self._redis_db.hset(self.name, "collaboration_type", value=collaboration_type.value)
        else:
            self._collaboration_type = collaboration_type
    
    def set_restart_sequence(self, restart_sequence: bool):
        """
        Set whether to restart a sequence of agents for this context.
        This is used by a sequential memory coordinator.

        Args:
            restart_sequence(bool): whether to restart a sequence of agents
        """
        if (self._use_redis == True):
            self._redis_db.hset(self.name, "restart_sequence", value=pickle.dumps(restart_sequence))
        else:
            self._restart_sequence = restart_sequence
    
    def get_restart_sequence(self) -> bool:
        """
        Get whether to restart the sequence for the chat uuid for this context.
        This is used by a sequential memory coordinator.

        Args:
            
        Returns:
            bool: whether to restart the sequence for the chat uuid for this context
        """
        if (self._use_redis == True):
            restart = self._redis_db.hget(self.name, "restart_sequence")
            if restart is not None:
                return pickle.loads(restart)
            else:
                return False
        else:
            return self._restart_sequence
        

class WiseAgentMetaData(WiseAgentsYAMLObject):
    ''' A WiseAgentMetaData is a class that represents metadata associated with an agent.
    Except description, all the metadata is optional and set to None as default.
    '''
    yaml_tag = u"!wiseagents.WiseAgentMetaData"
    def __new__(cls, *args, **kwargs):
        '''Create a new instance of the class, setting default values for the instance variables.'''
        obj = super().__new__(cls)
        obj._system_message = None
        obj._pre_user_message = None
        obj._post_user_message = None
        return obj
    def __init__(self, description : str, system_message: Optional[str] = None, pre_user_message: Optional[str] = None,
                 post_user_message: Optional[str] = None):
        ''' Initialize the metadata with the given system message.

        Args:
            description (str): a description of what the agent does
            system_message (Optional[str]): an optional system message that can be used by the agent when processing chat
            completions using its LLM
            pre_user_message (Optional[str]): an optional user message that can be used by the agent when processing chat
            completions using its LLM (e.g., when processing a request)
            post_user_message (Optional[str]): an optional user message that can be used by the agent when processing chat
            completions using its LLM (e.g., when processing a response)
        '''
        self._description = description
        self._system_message = system_message
        self._pre_user_message = pre_user_message
        self._post_user_message = post_user_message

    def __repr__(self):
        '''Return a string representation of the metadata.'''
        return (f"{self.__class__.__name__}(description={self.description}, system_message={self.system_message},"
                f"pre_user_message={self.pre_user_message},post_user_message={self.post_user_message})")
    
    def __eq__(self, value: object) -> bool:
        return self.__repr__() == value.__repr__()

    @property
    def description(self) -> str:
        """Get a description of what the agent does."""
        return self._description
    
    @property
    def system_message(self) -> Optional[str]:
        """Get the system message associated with the agent."""
        return self._system_message

    @property
    def pre_user_message(self) -> Optional[str]:
        """Get the pre user message associated with the agent."""
        return self._pre_user_message

    @property
    def post_user_message(self) -> Optional[str]:
        """Get the post user message associated with the agent."""
        return self._post_user_message


class WiseAgent(WiseAgentsYAMLObject):
    ''' A WiseAgent is an abstract class that represents an agent that can send and receive messages to and from other agents.
    '''
    
    def __new__(cls, *args, **kwargs):
        '''Create a new instance of the class, setting default values for the instance variables.'''
        obj = super().__new__(cls)
        enforce_no_abstract_class_instances(cls, WiseAgent)
        obj._llm = None
        obj._vector_db = None
        obj._graph_db = None
        obj._collection_name = "wise-agent-collection"
        return obj

    def __init__(self, name: str, metadata: WiseAgentMetaData, transport: WiseAgentTransport, llm: Optional[WiseAgentLLM] = None,
                 vector_db: Optional[WiseAgentVectorDB] = None,
                 collection_name: Optional[str] = "wise-agent-collection",
                 graph_db: Optional[WiseAgentGraphDB] = None):
        ''' 
        Initialize the agent with the given name, metadata, transport, LLM, vector DB, collection name, and graph DB.


        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata associated with the agent
            transport (WiseAgentTransport): the transport to use for sending and receiving messages
            llm (Optional[WiseAgentLLM]): the LLM associated with the agent
            vector_db (Optional[WiseAgentVectorDB]): the vector DB associated with the agent
            collection_name (Optional[str]) = "wise-agent-collection": the vector DB collection name associated with the agent
            graph_db (Optional[WiseAgentGraphDB]): the graph DB associated with the agent
        '''
        self._name = name
        self._metadata = metadata
        self._llm = llm
        self._vector_db = vector_db
        self._collection_name = collection_name
        self._graph_db = graph_db
        self._transport = transport
        self.start_agent()

    def start_agent(self):
        ''' Start the agent by setting the call backs and starting the transport.'''
        self.transport.set_call_backs(self.handle_request, self.process_event, self.process_error,
                                      self.process_response)
        self.transport.start()
        WiseAgentRegistry.register_agent(self.name, self.metadata)

    def stop_agent(self):
        ''' Stop the agent by stopping the transport and removing the agent from the registry.'''
        self.transport.stop()
        WiseAgentRegistry.unregister_agent(self.name)

    def __repr__(self):
        '''Return a string representation of the agent.'''
        return (f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self._collection_name}, graph_db={self.graph_db},)")

    def __eq__(self, value: object) -> bool:
        return isinstance(value, WiseAgent) and self.__repr__() == value.__repr__()

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def metadata(self) -> WiseAgentMetaData:
        """Get the metadata associated with the agent."""
        return self._metadata
    
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
        context = WiseAgentRegistry.get_context(message.context_name)
        self.transport.send_request(message, dest_agent_name)
        if context is not None:
            context.trace(message)
        else:
            logging.warning(f"Context {message.context_name} not found")

    def send_response(self, message: WiseAgentMessage, dest_agent_name):
        '''Send a response message to the destination agent with the given name.

        Args:
            message (WiseAgentMessage): the message to send
            dest_agent_name (str): the name of the destination agent'''
        message.sender = self.name
        context = WiseAgentRegistry.get_context(message.context_name)
        self.transport.send_response(message, dest_agent_name)
        context.trace(message)

    def handle_request(self, request: WiseAgentMessage) -> bool:
        """
        Callback method to handle the given request for this agent. This method optionally retrieves
        conversation history from the shared context depending on the type of collaboration the agent
        is involved in (i.e., sequential, phased, or independent) and passes this to the process_request
        method. Finally, it handles the response from the process_request method, ensuring the shared
        context is updated if necessary, and determines which agent to the send the response to, both
        depending on the type of collaboration the agent is involved in.

        Args:
            request (WiseAgentMessage): the request message to be processed

        Returns:
            True if the message was processed successfully, False otherwise
        """
        context = WiseAgentRegistry.get_context(request.context_name)
        logging.debug(f"Agent {self.name} received request in ctx: {context}")
        collaboration_type = context.collaboration_type
        conversation_history = self.get_conversation_history_if_needed(context, collaboration_type)
        response_str = self.process_request(request, conversation_history)
        return self.handle_response(response_str, request, context, collaboration_type)

    def get_conversation_history_if_needed(self, context: WiseAgentContext,
                                           collaboration_type: str) -> List[
        ChatCompletionMessageParam]:
        """
        Get the conversation history for the given chat id from the given context, depending on the
        type of collaboration the agent is involved in (i.e., sequential, phased, independent).

        Args:
            context (WiseAgentContext): the shared context
            collaboration_type (str): the type of collaboration this agent is involved in

        Returns:
            List[ChatCompletionMessageParam]: the conversation history for the given chat id if the agent
            is involved in a collaboration type that makes use of the conversation history and an empty list
            otherwise
        """
        if (collaboration_type == WiseAgentCollaborationType.PHASED
                or collaboration_type == WiseAgentCollaborationType.CHAT
                or collaboration_type == WiseAgentCollaborationType.SEQUENTIAL_MEMORY):
            # this agent is involved in phased collaboration or a chat, so it needs the conversation history
            return context.llm_chat_completion
        # for sequential collaboration and independent agents, the shared history is not needed
        return []

    @abstractmethod
    def process_request(self, request: WiseAgentMessage,
                        conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
        """
        Process the given request message to generate a response string.

        Args:
            request (WiseAgentMessage): the request message to be processed
            conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.

        Returns:
            Optional[str]: the response to the request message as a string or None if there is
            no string response yet
        """
        ...

    def handle_response(self, response_str: str, request: WiseAgentMessage,
                        context: WiseAgentContext, collaboration_type: str) -> bool:
        """
        Handles the given string response, ensuring the shared context is updated if necessary
        and determines which agent to the send the response to, both depending on the type of
        collaboration the agent is involved in (i.e., sequential, phased, or independent).

        Args:
            response_str (str): the string response to be handled
            request (WiseAgentMessage): the request message that generated the response
            context (WiseAgentContext): the shared context
            collaboration_type (str): the type of collaboration this agent is involved in

        Returns:
            True if the message was processed successfully, False otherwise
        """
        if response_str:
            if (collaboration_type == WiseAgentCollaborationType.PHASED
                    or collaboration_type == WiseAgentCollaborationType.CHAT):
                # add this agent's response to the shared context
                context.append_chat_completion(messages={"role": "assistant", "content": response_str})

                # let the sender know that this agent has finished processing the request
                self.send_response(
                    WiseAgentMessage(message=response_str, message_type=WiseAgentMessageType.ACK, sender=self.name,
                                     context_name=context.name), request.sender)
            elif (collaboration_type == WiseAgentCollaborationType.SEQUENTIAL 
                    or collaboration_type == WiseAgentCollaborationType.SEQUENTIAL_MEMORY):
                if collaboration_type == WiseAgentCollaborationType.SEQUENTIAL_MEMORY:
                    # add this agent's response to the shared context
                    context.append_chat_completion(messages={"role": "assistant", "content": response_str})
                next_agent = context.get_next_agent_in_sequence(self.name)
                if next_agent is None:
                    if context.get_restart_sequence():
                        next_agent = context.get_agents_sequence()[0]
                        logging.debug(f"Sequential coordination restarting")
                        self.send_request(
                            WiseAgentMessage(message=context.get_current_query(), sender=self.name,
                                             context_name=context.name), next_agent)
                        # clear the restart state for the context
                        context.set_restart_sequence(False)
                    else:
                        logging.debug(f"Sequential coordination complete - sending response from " + self.name + " to "
                                      + context.get_route_response_to())
                        self.send_response(WiseAgentMessage(message=response_str, sender=self.name,
                                                            context_name=context.name),
                                           context.get_route_response_to())
                else:
                    logging.debug(f"Sequential coordination continuing - sending response from " + self.name
                                  + " to " + next_agent)
                    self.send_request(
                        WiseAgentMessage(message=response_str, sender=self.name, context_name=context.name), next_agent)
            else:
                self.send_response(WiseAgentMessage(message=response_str, sender=self.name,
                                                    context_name=context.name),
                                   request.sender)
        return True

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



class WiseAgentRegistry:

    """
    A Registry to get available agents and running contexts
    """
    agents_metadata_dict : dict[str, WiseAgentMetaData] = {}
    contexts : dict[str, WiseAgentContext] = {}
    tools: dict[str, WiseAgentTool] = {}
    
    config: dict[str, Any] = {}
    
    redis_db : redis.Redis = None
    
    
    @classmethod
    def find_file(cls, file_name, config_directory=".wise-agents") -> str:
        """
        Find the file in the current directory or the home directory.
        """
        # Step 1: Check the current directory
        local_path= os.path.join(os.getcwd(), config_directory, file_name)
        if os.path.isfile(local_path):
            return local_path
        
        # Step 2: Check the home directory
        home_dir = os.path.expanduser("~")
        home_path = os.path.join(home_dir, config_directory,file_name)
        if os.path.isfile(home_path):
            return home_path
        
        # If the file is not found in any of these locations, throw an exception
        raise FileNotFoundError(f"File '{file_name}' not found in current directory, home directory, as '{config_directory}'/{file_name}.")
    
    @classmethod
    def get_config(cls) -> dict[str, Any]:
        """
        Get the configuration and initialize the redis database
        for more information see 
        https://wise-agents.github.io/wise_agents_architecture/#distributed-architecture
        """
        try: 
            if cls.config is None or cls.config == {}:
                file_name = cls.find_file(file_name="registry_config.yaml", config_directory=".wise-agents")
                cls.config : Dict[str, Any] = yaml.load(open(file_name), Loader=yaml.FullLoader)
            if cls.config.get("use_redis") == True and cls.redis_db is None:
                if (cls.config.get("redis_ssl") is True):
                    cls.redis_db = redis.Redis(
                    host=cls.config["redis_host"], port=cls.config["redis_port"],
                    username=cls.config["redis_username"], # use your Redis user. More info https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/
                    password=cls.config["redis_password"], # use your Redis password
                    ssl=True,
                    ssl_certfile=cls.config["redis_ssl_certfile"],
                    ssl_keyfile=cls.config["redis_ssl_keyfile"],
                    ssl_ca_certs=cls.config["redis_ssl_ca_certs"])

                else:
                    cls.redis_db = redis.Redis(host=cls.config["redis_host"], port=cls.config["redis_port"])
            return cls.config
        except Exception as e:
            logging.error(e)
            exit(1)
    
    @classmethod
    def register_agent(cls, agent_name : str, agent_metadata :WiseAgentMetaData):
        """
        Register an agent with the registry
        """
        if (cls.get_config().get("use_redis") == True):
            pipe = cls.redis_db.pipeline(transaction=True)
            while True:
                pipe.watch("agents")
                try:
                    if(pipe.hexists("agents", agent_name) == True):
                        pipe.unwatch()
                        raise NameError(f"Agent with name {agent_name} already exists")
                    else:
                        pipe.multi()
                        pipe.hset("agents", key=agent_name, value=pickle.dumps(agent_metadata))
                        pipe.execute()
                    return
                except redis.WatchError:
                    logging.debug("WatchError in register_agent")
                    continue
        else:
            if cls.agents_metadata_dict.get(agent_name) is not None:
                raise NameError(f"Agent with name {agent_name} already exists")
        cls.agents_metadata_dict[agent_name] = agent_metadata
    @classmethod    
    def register_context(cls, context : WiseAgentContext):
        """
        Register a context with the registry
        """
        if (cls.does_context_exist(context.name) == True):
            raise NameError(f"Context with name {context.name} already exists")
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.hset("contexts", key=context.name, value=pickle.dumps(context))
        else:
            cls.contexts[context.name] = context
    @classmethod    
    def fetch_agents_metadata_dict(cls) -> dict [str, WiseAgentMetaData]:
        """
        Get the dict with the agent names as keys and metadata as values
        """
        if (cls.get_config().get("use_redis") == True):
            redis_dict = cls.redis_db.hgetall("agents")
            return_dictionary : Dict[str, WiseAgentMetaData]= {}
            for key in redis_dict:
                return_dictionary[key.decode('utf-8')] = pickle.loads(redis_dict[key])
            return return_dictionary
        else:
            return cls.agents_metadata_dict
    
    @classmethod
    def get_contexts(cls) -> dict [str, WiseAgentContext]:
        """
        Get the list of contexts
        """
        if (cls.get_config().get("use_redis") == True):
            dictionary = cls.redis_db.hgetall("contexts")
            return_dictionary : Dict[str, WiseAgentContext]= {}
            for key in dictionary:
                 return_dictionary[key] = pickle.loads(dictionary.get(key))
            return return_dictionary
        else:
            return cls.contexts
    
    @classmethod
    def get_agent_metadata(cls, agent_name: str) -> WiseAgentMetaData:
        """
        Get the agent metadata for the agent with the given name
        """
        if (cls.get_config().get("use_redis") == True):
            return_byte = cls.redis_db.hget("agents", key=agent_name)
            if return_byte is not None:
                return pickle.loads(return_byte)
            else:  
                return None
        else:
            return cls.agents_metadata_dict.get(agent_name) 
    
    @classmethod
    def get_context(cls, context_name: str) -> WiseAgentContext:
        """ Get the context with the given name """
        context : WiseAgentContext = None
        if (cls.get_config().get("use_redis") == True):
            ctx = cls.redis_db.hget("contexts", key=context_name)
            if ctx is not None:
                context : WiseAgentContext = pickle.loads(ctx)
            else:
                context = None
        else:
            context = cls.contexts.get(context_name)
        return context

    @classmethod
    def create_context(cls, context_name: str) -> WiseAgentContext:
        """ Create the context with the given name """
        if ('_' in context_name):
            raise NameError(f"First level Context name {context_name} cannot contain an underscore. If you are trying to create a sub context, use create_sub_context method")
        if (cls.does_context_exist(context_name) == False):
            return WiseAgentContext(context_name, cls.config)
        else:
            raise NameError(f"Context with name {context_name} already exists")
    
    @classmethod
    def create_sub_context(cls, parent_context_name: str, sub_context_name: str) -> WiseAgentContext:
        """
        Create a sub context with the given name under the parent context with the given name
        Args:
            parent_context_name (str): the name of the parent context
            sub_context_name (str): the name of the sub context
        Returns:
            WiseAgentContext: the sub context
        """
        if ('_' in sub_context_name):
            raise NameError(f"Sub Context name {sub_context_name} cannot contain an underscore")
        if cls.does_context_exist(parent_context_name):
            logging.debug(f"set_collaboration_type (0.0) cls.config: {cls.config}")
            sub_context = WiseAgentContext(f'{parent_context_name}_{sub_context_name}', cls.config)
            logging.debug(f"set_collaboration_type (0.1) sub_context: {sub_context} _use_redis: {sub_context._use_redis}")
    
            return sub_context
        else:
            message = f"Parent context with name {parent_context_name} does not exist"
            raise NameError(message)


    @classmethod
    def remove_context(cls, context_name: str, merge_chat_to_parent: Optional[bool] = False) -> Optional[WiseAgentContext]:
        """
        Remove the context from the registry

        Args:
            context_name (str): the name of the context
            merge_chat_to_parent (Optional[bool]): whether to merge the chat completion of the context to the parent context
        Returns:
            Optional[WiseAgentContext]: the parent context if it exists and merge_chat_to_parent = True. Otherwise return None

        """
        parent_context_name = None
        parent_context = None
        if ("_" in context_name and merge_chat_to_parent): # it has a parent context
            parent_context_name = "_".join(context_name.split("_")[:-1])
            parent_context = cls.get_context(parent_context_name)
            context = cls.get_context(context_name)
            if parent_context is not None and context is not None:
                parent_context.append_chat_completion(context.llm_chat_completion)
            else:
                raise NameError(f"Parent context with name {parent_context_name} or context with name {context_name} does not exist")
        logging.info(f"Removing context {context_name}")    
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.hdel("contexts", context_name)
        else:
            cls.contexts.pop(context_name)
        return parent_context
    
    @classmethod
    def does_context_exist(cls, context_name: str) -> bool:
        """
        Get the context with the given name
        """
        if (cls.get_config().get("use_redis") == True):
            return cls.redis_db.hexists("contexts", key=context_name)
        else:
            if  cls.contexts.get(context_name) is None:
                return False
            else:
                return True
    
    @classmethod
    def unregister_agent(cls, agent_name: str):
        """
        Remove the agent from the registry this should be used only on agents which already stopped transport connection
        """
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.hdel("agents", agent_name)
        else:
            if cls.agents_metadata_dict.get(agent_name) is not None:
                cls.agents_metadata_dict.pop(agent_name)
        
    @classmethod
    def register_tool(cls, tool : WiseAgentTool):
        """
        Register a tool with the registry
        """
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.hset("tools", key=tool.name, value=pickle.dumps(tool))
        else:
            cls.tools[tool.name] = tool
    
    @classmethod
    def get_tools(cls) -> dict[str, WiseAgentTool]:
        """
        Get the list of tools
        """
        if (cls.get_config().get("use_redis") == True):
            dictionary = cls.redis_db.hgetall("tools")
            return_dictionary : Dict[str, WiseAgentTool]= {}
            for key in dictionary:
                 return_dictionary[key] = pickle.loads(dictionary.get(key))
            return return_dictionary
        else:
            return cls.tools
    
    @classmethod
    def get_tool(cls, tool_name: str) -> WiseAgentTool:
        """
        Get the tool with the given name
        """
        if (cls.get_config().get("use_redis") == True):
            pipe = cls.redis_db.pipeline(transaction=True)
            piped_res= pipe.hexists("tools", key=tool_name).hget("tools", key=tool_name).execute()
            if piped_res[0]:
                return pickle.loads(piped_res[1])
            else:
                return None
        else:
            return cls.tools.get(tool_name)

    @classmethod
    def get_agent_names_and_descriptions(cls) -> List[str]:
        """
        Get the list of agent names and descriptions.

        Returns:
            List[str]: the list of agent descriptions
        """
        agent_descriptions = []
        for agent_name, agent_metadata in cls.fetch_agents_metadata_dict().items():
            agent_descriptions.append(f"Agent Name: {agent_name} Agent Description: {agent_metadata.description}")

        return agent_descriptions


