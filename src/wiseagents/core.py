import copy
from abc import ABC, abstractmethod
import json
import logging
import os
import pickle
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import UUID

import redis


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

    def __new__(cls, *args, **kwargs):
        '''Create a new instance of the class, setting default values for the instance variables.'''
        obj = super().__new__(cls)
        obj._llm = None
        obj._vector_db = None
        obj._graph_db = None
        obj._collection_name = "wise-agent-collection"
        obj._system_message = None
        return obj

    def __init__(self, name: str, description: str, transport: WiseAgentTransport, llm: Optional[WiseAgentLLM] = None,
                 vector_db: Optional[WiseAgentVectorDB] = None, collection_name: Optional[str] = "wise-agent-collection",
                 graph_db: Optional[WiseAgentGraphDB] = None, system_message: Optional[str] = None):
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
            system_message Optional(str): an optional system message that can be used by the agent when processing chat
            completions using its LLM
        '''
        self._name = name
        self._description = description
        self._llm = llm
        self._vector_db = vector_db
        self._collection_name = collection_name
        self._graph_db = graph_db
        self._transport = transport
        self._system_message = system_message
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
                f"vector_db={self.vector_db}, collection_name={self._collection_name}, graph_db={self.graph_db},"
                f"system_message={self.system_message})")
    
    def __eq__(self, value: object) -> bool:
        return isinstance(value, WiseAgent) and self.__repr__() == value.__repr__()
    
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

    @property
    def system_message(self) -> Optional[str]:
        """Get the system message associated with the agent."""
        return self._system_message

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
    
    ''' A WiseAgentContext is a class that represents a context in which agents can communicate with each other.
    '''
    
    _message_trace : List[WiseAgentMessage] = []
    _participants : List[WiseAgent] = []
    
    # Maps a chat uuid to a list of chat completion messages
    _llm_chat_completion : Dict[str, List[ChatCompletionMessageParam]] = {}
    
    # Maps a chat uuid to a list of tool names that need to be executed
    _llm_required_tool_call : Dict[str, List[str]] = {}
    
    # Maps a chat uuid to a list of available tools in chat
    _llm_available_tools_in_chat : Dict[str, List[ChatCompletionToolParam]] = {}

    # Maps a chat uuid to a list of agent names that need to be executed in sequence
    # Used by a sequential coordinator
    _agents_sequence : Dict[str, List[str]] = {}

    # Maps a chat uuid to the agent where the final response should be routed to
    # Used by both a sequential coordinator and a phased coordinator
    _route_response_to : Dict[str, str] = {}

    # Maps a chat uuid to a list that contains a list of agent names to be executed for each phase
    # Used by a phased coordinator
    _agent_phase_assignments : Dict[str, List[List[str]]] = {}

    # Maps a chat uuid to the current phase. Used by a phased coordinator.
    _current_phase : Dict[str, int] = {}

    # Maps a chat uuid to a list of agent names that need to be executed for the current phase
    # Used by a phased coordinator
    _required_agents_for_current_phase : Dict[str, List[str]] = {}

    # Maps a chat uuid to a list containing the queries attempted for each iteration executed by
    # the phased coordinator
    _queries : Dict[str, List[str]] = {}
    
    _redis_db : redis.Redis = None
    _use_redis : bool = False
    _config : Dict[str, Any] = {}
    
    def __init__(self, name: str, config : Optional[Dict[str,Any]] = {"use_redis": False}):
        ''' Initialize the context with the given name.

        Args:
            name (str): the name of the context'''
        self._name = name
        self._config = config
        if config.get("use_redis") == True and self._redis_db is None:
            self._redis_db = redis.Redis(host=self._config["redis_host"], port=self._config["redis_port"])
            self._use_redis = True
            
        WiseAgentRegistry.register_context(self)
    
    def __repr__(self) -> str:
        '''Return a string representation of the context.'''
        return (f"{self.__class__.__name__}(name={self.name}, message_trace={self.message_trace},"
                f"participants={self.participants}, llm_chat_completion={self.llm_chat_completion},"
                f"llm_required_tool_call={self.llm_required_tool_call}, llm_available_tools_in_chat={self.llm_available_tools_in_chat},"
                f"agents_sequence={self._agents_sequence}, route_response_to={self._route_response_to},"
                f"agent_phase_assignments={self._agent_phase_assignments}, current_phase={self._current_phase},"
                f"required_agents_for_current_phase={self._required_agents_for_current_phase}, queries={self._queries})")
    def __eq__(self, value: object) -> bool:
        return isinstance(value, WiseAgentContext) and self.__repr__() == value.__repr__()
    
    def __getstate__(self) -> object:
        '''Get the state of the context.'''
        state = self.__dict__.copy()
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
        
    @property   
    def name(self) -> str:
        """Get the name of the context."""
        return self._name
    
    @property
    def message_trace(self) -> List[WiseAgentMessage]:
        """Get the message trace of the context."""
        if (self._use_redis == True):
            return_list : List[WiseAgentMessage] = []
            redis_list = self._redis_db.lrange("message_trace", 0, -1)
            for message in redis_list:
                return_list.append(pickle.loads(message))
            return return_list
        else:
            return self._message_trace
        
        
    @property
    def participants(self) -> List[WiseAgent]:
        """Get the participants of the context."""
        if (self._use_redis == True):
            return_list : List[WiseAgent] = []
            redis_list = self._redis_db.lrange("participants", 0, -1)
            for message in redis_list:
                return_list.append(pickle.loads(message))
            return return_list
        else:
            return self._participants
    
    @property
    def llm_chat_completion(self) -> Dict[str, List[ChatCompletionMessageParam]]:
        """Get the LLM chat completion of the context."""
        if (self._use_redis == True):
            return_dict : Dict[str, List[ChatCompletionMessageParam]] = {}
            redis_dict = self._redis_db.hgetall("llm_chat_completion")
            for key in redis_dict:
                return_dict[key.decode('utf-8')] = pickle.loads(redis_dict[key])
            return return_dict
        else:
            return self._llm_chat_completion
    
    def add_participant(self, agent: WiseAgent):
        '''Add a participant to the context.

        Args:
            agent (WiseAgent): the agent to add'''
        if agent not in self.participants:    
            if (self._use_redis == True):
                self._redis_db.rpush("participants", pickle.dumps(agent))
            else:
                self._participants.append(agent)
    
    def append_chat_completion(self, chat_uuid: str, messages: Iterable[ChatCompletionMessageParam]):
        '''Append chat completion to the context.

        Args:
            chat_uuid (str): the chat uuid
            messages (Iterable[ChatCompletionMessageParam]): the messages to append'''
            
        if (self._use_redis == True):
            pipe = self._redis_db.pipeline(transaction=True)
            if(self._redis_db.hexists("llm_chat_completion", key=chat_uuid) == False):
                self._redis_db.hset("llm_chat_completion", key=chat_uuid, value=pickle.dumps([messages]))
                pipe.execute()
            else:
                while True:
                    try:
                        lock = f"llm_chat_completion_{chat_uuid}_lock"
                        pipe.watch("llm_chat_completion")
                        redis_stored_messages = pipe.hget("llm_chat_completion", key=chat_uuid)
                        stored_messages : List[ChatCompletionMessageParam] = pickle.loads(redis_stored_messages)
                        stored_messages.append(messages)
                        pipe.multi()
                        pipe.hset("llm_chat_completion", key=chat_uuid, value=pickle.dumps(stored_messages))
                        pipe.execute()
                        break
                    except redis.WatchError:
                        raise redis.WatchError
                        logging.warning("WatchError in append_chat_completion")
                        continue
        else:
            if chat_uuid not in self._llm_chat_completion:
                self._llm_chat_completion[chat_uuid] = []
            self._llm_chat_completion[chat_uuid].append(messages)
    
    @property
    def llm_required_tool_call(self) -> Dict[str, List[str]]:
        """Get the LLM required tool call of the context.
        return Dict[str, List[str]]"""
        if (self._use_redis == True):
            redis_dict = self._redis_db.hgetall("llm_required_tool_call")
            return_dict : Dict[str, List[str]] = {}
            for key in redis_dict:
                return_dict[key] = pickle.loads(redis_dict[key])
            return return_dict
        else:
            return self._llm_required_tool_call
    
    def append_required_tool_call(self, chat_uuid: str, tool_name: str):
        '''Append required tool call to the context.

        Args:
            chat_uuid (str): the chat uuid
            tool_name (str): the tool name to append'''
        if (self._use_redis == True):
            pipe = self._redis_db.pipeline(transaction=True)
            if (self._redis_db.hexists("llm_required_tool_call", key=chat_uuid) == False):
                self._redis_db.hset("llm_required_tool_call", key=chat_uuid, value=pickle.dumps([tool_name]))
                pipe.execute()
            else :
                while True:
                    try:
                        pipe.watch("llm_required_tool_call")
                        redis_stored_tool_names = pipe.hget("llm_required_tool_call", key=chat_uuid)
                        stored_tool_names : List[str] = pickle.loads(redis_stored_tool_names)
                        stored_tool_names.append(tool_name)
                        pipe.multi()
                        pipe.hset("llm_required_tool_call", key=chat_uuid, value=pickle.dumps(stored_tool_names))
                        pipe.execute()
                        break
                    except redis.WatchError:
                        logging.warning("WatchError in append_required_tool_call")
                        continue
        else:
            if chat_uuid not in self.llm_required_tool_call:
                self._llm_required_tool_call[chat_uuid] = []
            self._llm_required_tool_call[chat_uuid].append(tool_name)
    
    def remove_required_tool_call(self, chat_uuid: str, tool_name: str):
        '''Remove required tool call from the context.

        Args:
            chat_uuid (str): the chat uuid
            tool_name (str): the tool name to remove'''
        if (self._use_redis == True):
            while True:
                try:
                    pipe = self._redis_db.pipeline(transaction=True)
                    pipe.watch("llm_required_tool_call")
                    if (pipe.hexists("llm_required_tool_call", key=chat_uuid) == False):
                        pipe.unwatch()
                        return
                    redis_stored_tool_names = pipe.hget("llm_required_tool_call", key=chat_uuid)
                    if (redis_stored_tool_names == None):
                        stored_tool_names : List[str] = []
                    else:
                        stored_tool_names : List[str] = pickle.loads(redis_stored_tool_names)
                        stored_tool_names.remove(tool_name)
                    pipe.multi()
                    if len(stored_tool_names) == 0:
                        pipe.hdel("llm_required_tool_call", chat_uuid)
                    else:
                        pipe.hset("llm_required_tool_call", key=chat_uuid, value=pickle.dumps(stored_tool_names))
                    pipe.execute()
                    break
                except redis.WatchError:
                    logging.warning("WatchError in remove_required_tool_call")
                    continue
        if chat_uuid in self._llm_required_tool_call:
            self._llm_required_tool_call[chat_uuid].remove(tool_name)
            if len(self._llm_required_tool_call[chat_uuid]) == 0:
                self._llm_required_tool_call.pop(chat_uuid)
                
    def get_required_tool_calls(self, chat_uuid: str) -> List[str]:
        '''Get required tool calls from the context.

        Args:
            chat_uuid (str): the chat uuid
            return List[str]'''
        if (self._use_redis == True):
            llm_req_tools = self._redis_db.hget("llm_required_tool_call", key=chat_uuid)
            if (llm_req_tools is not None):
                return pickle.loads(llm_req_tools)
            else:
                return []
        if chat_uuid in self._llm_required_tool_call:
            return self._llm_required_tool_call[chat_uuid]
        else:
            return []   
        
    @property
    def llm_available_tools_in_chat(self) -> Dict[str, List[ChatCompletionToolParam]]:
        """Get the LLM available tools in chat of the context."""
        if (self._use_redis == True):
            redis_dict = self._redis_db.hgetall("llm_available_tools_in_chat")
            return_dict : Dict[str, List[ChatCompletionToolParam]] = {}
            for key in redis_dict:
                return_dict[key] = pickle.loads(redis_dict[key])
            return return_dict
        return self._llm_available_tools_in_chat
    
    def append_available_tool_in_chat(self, chat_uuid: str, tools: Iterable[ChatCompletionToolParam]):
        '''Append available tool in chat to the context.

        Args:
            chat_uuid (str): the chat uuid
            tools (Iterable[ChatCompletionToolParam]): the tools to append'''
        if (self._use_redis == True):
            while True:
                try:
                    pipe = self._redis_db.pipeline(transaction=True)
                    pipe.watch("llm_available_tools_in_chat")
                    if (pipe.hexists("llm_available_tools_in_chat", key=chat_uuid) == False):
                        pipe.multi()    
                        pipe.hset("llm_available_tools_in_chat", key=chat_uuid, value=pickle.dumps([tools]))
                        pipe.execute()
                        break
                    else :
                        redis_stored_tools = pipe.hget("llm_available_tools_in_chat", key=chat_uuid)
                        stored_tools : List[ChatCompletionToolParam] = pickle.loads(redis_stored_tools)
                        stored_tools.append(tools)
                        pipe.multi()
                        pipe.hset("llm_available_tools_in_chat", key=chat_uuid, value=pickle.dumps(stored_tools))
                        pipe.execute()
                        break
                except redis.WatchError:
                    logging.warning("WatchError in append_available_tool_in_chat")
                    continue
        else:
            if chat_uuid not in self._llm_available_tools_in_chat:
                self._llm_available_tools_in_chat[chat_uuid] = []
            self._llm_available_tools_in_chat[chat_uuid].append(tools)
    
    def get_available_tools_in_chat(self, chat_uuid: str) -> List[ChatCompletionToolParam]:
        '''Get available tools in chat from the context.

        Args:
            chat_uuid (str): the chat uuid
            return List[ChatCompletionToolParam]'''
        if (self._use_redis == True):
            llm_av_tools = self._redis_db.hget("llm_available_tools_in_chat", key=chat_uuid)   
            if (llm_av_tools is not None):
                return pickle.loads(llm_av_tools)
            else:
                return []
        else:
            if chat_uuid in self._llm_available_tools_in_chat:
                return self._llm_available_tools_in_chat[chat_uuid]
            else:
                return []

    def get_agents_sequence(self, chat_uuid: str) -> List[str]:
        """
        Get the sequence of agents for the given chat uuid for this context. This is used by a sequential
        coordinator to execute its agents in a specific order, passing the output from one agent in the sequence
        to the next agent in the sequence.

        Args:
            chat_uuid (str): the chat uuid

        Returns:
            List[str]: the sequence of agents names or an empty list if no sequence has been set for this context
        """
        if (self._use_redis == True):
            agent_sequence = self._redis_db.hget("agents_sequence", key=chat_uuid)
            if (agent_sequence is not None):
                return pickle.loads(agent_sequence)
            else:
                return []
        else:
            if chat_uuid in self._agents_sequence:
                return self._agents_sequence[chat_uuid]
            return []

    def set_agents_sequence(self, chat_uuid: str, agents_sequence: List[str]):
        """
        Set the sequence of agents for the given chat uuid for this context. This is used by
        a sequential coordinator to execute its agents in a specific order, passing the output
        from one agent in the sequence to the next agent in the sequence.

        Args:
            chat_uuid (str): the chat uuid
            agents_sequence (List[str]): the sequence of agent names
        """
        if (self._use_redis == True):
            self._redis_db.hset("agents_sequence", key=chat_uuid, value=pickle.dumps(agents_sequence))
        else:
            self._agents_sequence[chat_uuid] = agents_sequence

    def get_route_response_to(self, chat_uuid: str) -> Optional[str]:
        """
        Get the name of the agent where the final response should be routed to for the given chat uuid for this
        context. This is used by a sequential coordinator and a phased coordinator.

        Returns:
            Optional[str]: the name of the agent where the final response should be routed to or None if no agent is set
        """
        if (self._use_redis == True):
            route = self._redis_db.hget("route_response_to", key=chat_uuid)
            if (route is not None):
                return pickle.loads(route)
            else:
                return None
        else: 
            if chat_uuid in self._route_response_to:
                return self._route_response_to[chat_uuid]
            else:
                return None

    def set_route_response_to(self, chat_uuid: str, agent: str):
        """
        Set the name of the agent where the final response should be routed to for the given chat uuid for this
        context. This is used by a sequential coordinator and a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid
            agent (str): the name of the agent where the final response should be routed to
        """
        if (self._use_redis == True):
            self._redis_db.hset("route_response_to", key=chat_uuid, value=pickle.dumps(agent))
        else:
            self._route_response_to[chat_uuid] = agent

    def get_next_agent_in_sequence(self, chat_uuid: str, current_agent: str):
        """
        Get the name of the next agent in the sequence of agents for the given chat uuid for this context.
        This is used by a sequential coordinator to determine the name of the next agent to execute.

        Args:
            chat_uuid (str): the chat uuid
            current_agent (str): the name of the current agent

        Returns:
            str: the name of the next agent in the sequence after the current agent or None if there are no remaining
            agents in the sequence after the current agent
        """
        agents_sequence = self.get_agents_sequence(chat_uuid)
        if current_agent in agents_sequence:
            current_agent_index = agents_sequence.index(current_agent)
            next_agent_index = current_agent_index + 1
            if next_agent_index < len(agents_sequence):
                return agents_sequence[next_agent_index]
        return None

    def get_agent_phase_assignments(self, chat_uuid: str) -> List[List[str]]:
        """
        Get the agents to be executed in each phase for the given chat uuid for this context. This is used
        by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid

        Returns:
            List[List[str]]: The agents to be executed in each phase, represented as a list of lists, where the
            size of the outer list corresponds to the number of phases and each element in the list is a list of
            agent names for that phase. An empty list is returned if no phases have been set for the
            given chat uuid
        """
        if (self._use_redis == True):
            agent_phase = self._redis_db.hget("agent_phase_assignments", key=chat_uuid)
            if (agent_phase is not None):
                return pickle.loads(agent_phase)
            else:
                return []
        else:
            if chat_uuid in self._agent_phase_assignments:
                return self._agent_phase_assignments.get(chat_uuid)
            return []

    def set_agent_phase_assignments(self, chat_uuid: str, agent_phase_assignments: List[List[str]]):
        """
        Set the agents to be executed in each phase for the given chat uuid for this context. This is used
        by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid
            agent_phase_assignments (List[List[str]]): The agents to be executed in each phase, represented as a
            list of lists, where the size of the outer list corresponds to the number of phases and each element
            in the list is a list of agent names for that phase.
        """
        if (self._use_redis == True):
            self._redis_db.hset("agent_phase_assignments", key=chat_uuid, value=pickle.dumps(agent_phase_assignments))
        else:
            self._agent_phase_assignments[chat_uuid] = agent_phase_assignments

    def get_current_phase(self, chat_uuid: str) -> int:
        """
        Get the current phase for the given chat uuid for this context. This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid

        Returns:
            int: the current phase, represented as an integer in the zero-indexed list of phases
        """
        if (self._use_redis == True):
            cur_phase = self._redis_db.hget("current_phase", key=chat_uuid)
            if (cur_phase is not None):
                return pickle.loads(cur_phase)
            else:
                return None
        else:
            return self._current_phase.get(chat_uuid)

    def set_current_phase(self, chat_uuid: str, phase: int):
        """
        Set the current phase for the given chat uuid for this context. This method also
        sets the required agents for the current phase. This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid
            phase (int): the current phase, represented as an integer in the zero-indexed list of phases
        """
        if (self._use_redis == True):
            self._redis_db.pipeline(transaction=True)\
                .hset("current_phase", key=chat_uuid, value=pickle.dumps(phase))\
                .hset("required_agents_for_current_phase", key=chat_uuid, value=pickle.dumps(self.get_agent_phase_assignments(chat_uuid)[phase]))\
                .execute()
        else:
            self._current_phase[chat_uuid] = phase
            self._required_agents_for_current_phase[chat_uuid] = copy.deepcopy(self._agent_phase_assignments[chat_uuid][phase])

    def get_agents_for_next_phase(self, chat_uuid: str) -> Optional[List]:
        """
        Get the list of agents to be executed for the next phase for the given chat uuid for this context.
        This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid

        Returns:
            Optional[List[str]]: the list of agent names for the next phase or None if there are no more phases
        """
        current_phase = self.get_current_phase(chat_uuid)
        next_phase = current_phase + 1
        if next_phase < len(self.get_agent_phase_assignments(chat_uuid)):
            self.set_current_phase(chat_uuid, next_phase)
            return self.get_agent_phase_assignments(chat_uuid)[next_phase]
        return None

    def get_required_agents_for_current_phase(self, chat_uuid: str) -> List[str]:
        """
        Get the list of agents that still need to be executed for the current phase for the given chat uuid for this
        context. This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid

        Returns:
            List[str]: the list of agent names that still need to be executed for the current phase or an empty list
            if there are no remaining agents that need to be executed for the current phase
        """
        if (self._use_redis == True):
            req_agent = self._redis_db.hget("required_agents_for_current_phase", key=chat_uuid)
            if (req_agent is not None):
                return pickle.loads(req_agent)
            else:
                return []
        else:
            if chat_uuid in self._required_agents_for_current_phase:
                return self._required_agents_for_current_phase.get(chat_uuid)
            return []

    def remove_required_agent_for_current_phase(self, chat_uuid: str, agent_name: str):
        """
        Remove the given agent from the list of required agents for the current phase for the given chat uuid for this
        context. This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid
            agent_name (str): the name of the agent to remove
        """
        if (self._use_redis == True):
            while True:
                try:
                    pipe = self._redis_db.pipeline(transaction=True)
                    pipe.watch("required_agents_for_current_phase")
                    if (pipe.hexists("required_agents_for_current_phase", key=chat_uuid) == False):
                        pipe.unwatch()
                        return
                    redis_stored_agents = pipe.hget("required_agents_for_current_phase", key=chat_uuid)
                    stored_agents : List[str] = pickle.loads(redis_stored_agents)
                    stored_agents.remove(agent_name)
                    pipe.multi()
                    if len(stored_agents) == 0:
                        pipe.hdel("required_agents_for_current_phase", chat_uuid)
                    else:
                        pipe.hset("required_agents_for_current_phase", key=chat_uuid, value=pickle.dumps(stored_agents))
                    pipe.execute()
                    break
                except redis.WatchError:
                    logging.warning("WatchError: Retrying to remove agent")
                    continue
        else:
            if chat_uuid in self._required_agents_for_current_phase:
                self._required_agents_for_current_phase.get(chat_uuid).remove(agent_name)

    def get_current_query(self, chat_uuid: str) -> Optional[str]:
        """
        Get the current query for the given chat uuid for this context. This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid

        Returns:
            Optional[str]: the current query or None if there is no current query
        """
        if (self._use_redis == True):
            queries = self._redis_db.hget("queries", key=chat_uuid)
            if (queries is not None):
                return_list : List[str] = pickle.loads(queries)
                return return_list[-1]
            else:
                return None
        else:
            if chat_uuid in self._queries:
                if self._queries.get(chat_uuid):
                    # return the last query
                    return self._queries.get(chat_uuid)[-1]
            else:
                return None

    def add_query(self, chat_uuid: str, query: str):
        """
        Add the current query for the given chat uuid for this context. This is used by a phased coordinator.

        Args:
            chat_uuid (str): the chat uuid
            query (str): the current query
        """
        if (self._use_redis == True):
            while True:
                try:
                    pipe = self._redis_db.pipeline(transaction=True)
                    pipe.watch("queries")
                    if (pipe.hexists("queries", key=chat_uuid) == False):
                        pipe.hset("queries", key=chat_uuid, value=pickle.dumps([query]))
                    else :
                        redis_stored_queries = pipe.hget("queries", key=chat_uuid)
                        stored_queries : List[str] = pickle.loads(redis_stored_queries)
                        stored_queries.append(query)
                        pipe.multi()
                        pipe.hset("queries", key=chat_uuid, value=pickle.dumps(stored_queries))
                    pipe.execute()
                    break
                except redis.WatchError:
                    logging.warning("WatchError: Retrying to add query")
                    continue
        else:
            if chat_uuid not in self._queries:
                self._queries[chat_uuid] = []
            self._queries[chat_uuid].append(query)

    def get_queries(self, chat_uuid: str) -> List[str]:
        """
        Get the queries attempted for the given chat uuid for this context. This is used by a phased coordinator.

        Returns:
            List[str]: the queries attempted for the given chat uuid for this context
        """
        if (self._use_redis == True):
            query = self._redis_db.hget("queries", key=chat_uuid)
            if (query is not None):
                return pickle.loads(query)
            else:
                return []
        if chat_uuid in self._queries:
            return self._queries.get(chat_uuid)
        else:
            return []


class WiseAgentRegistry:

    """
    A Registry to get available agents and running contexts
    """
    agents : dict[str, WiseAgent] = {}
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
    def register_agent(cls,agent : WiseAgent):
        """
        Register an agent with the registry
        """
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.hset("agents", key=agent.name, value=pickle.dumps(agent))
        else:
            cls.agents[agent.name] = agent
    @classmethod    
    def register_context(cls, context : WiseAgentContext):
        """
        Register a context with the registry
        """
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.hset("contexts", key=context.name, value=pickle.dumps(context))
        else:
            cls.contexts[context.name] = context
    @classmethod    
    def get_agents(cls) -> dict [str, WiseAgent]:
        """
        Get the list of agents
        """
        if (cls.get_config().get("use_redis") == True):
            dictionary = cls.redis_db.hgetall("agents")
            return_dictionary : Dict[str, WiseAgent]= {}
            for key in dictionary:
                return_dictionary[key.decode("utf-8")] = pickle.loads(dictionary.get(key))
            return return_dictionary   
        else:
            return cls.agents
    
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
    def get_agent(cls, agent_name: str) -> WiseAgent:
        """
        Get the agent with the given name
        """
        if (cls.get_config().get("use_redis") == True):
            agent = cls.redis_db.hget("agents", key=agent_name)
            if agent is not None:
                return pickle.loads(agent)
            else:
                return None
        else:
            return cls.agents.get(agent_name) 
    
    @classmethod
    def get_or_create_context(cls, context_name: str) -> WiseAgentContext:
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
        if context is None:
            # context creation will also register the context in the registry
            return WiseAgentContext(context_name, cls.config)
        else:
            return context
        
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
    def remove_agent(cls, agent_name: str):
        """
        Remove the agent from the registry
        """
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.hdel("agents", agent_name)
        else:
            cls.agents.pop(agent_name)
        
    @classmethod
    def remove_context(cls, context_name: str):
        """
        Remove the context from the registry
        """
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.hdel("contexts", context_name)
        else:
            cls.contexts.pop(context_name)
    
    @classmethod
    def clear_agents(cls):
        """
        Clear all agents from the registry
        """
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.delete("agents")
        else:
            cls.agents.clear()
    
    @classmethod
    def clear_contexts(cls):
        """
        Clear all contexts from the registry
        """
        if (cls.get_config().get("use_redis") == True):
            cls.redis_db.delete("contexts")
        else:
            cls.contexts.clear()
        
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
        for agent_name, agent in cls.get_agents().items():
            agent_descriptions.append("Agent Name: " + agent_name + " Agent Description: " + agent.description)

        return agent_descriptions


