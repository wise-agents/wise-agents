from typing import Dict, Iterable, Optional

import openai
from openai.types.chat import ChatCompletionMessageParam, ChatCompletion, ChatCompletionToolParam

from wiseagents.llm.wise_agent_remote_LLM import WiseAgentRemoteLLM


class OpenaiAPIWiseAgentLLM(WiseAgentRemoteLLM):
    '''A class to define a WiseAgentLLM that uses the OpenAI API.'''
    client = None
    yaml_tag = u'!wiseagents.llm.OpenaiAPIWiseAgentLLM'


    
    def __new__(cls, *args, **kwargs):
        '''Create a new instance of the class, setting default values for the instance variables.'''
        obj = super().__new__(cls)
        obj._api_key = "sk-no-key-required"
        obj._remote_address = "http://localhost:8001/v1"
        obj._openai_config = {}
        return obj

    def __init__(self, system_message, model_name, remote_address = "http://localhost:8001/v1", api_key: Optional[str]="sk-no-key-required", openai_config: Optional[Dict[str,str]]={}):
        '''Initialize the agent.

        Args:
            system_message (str): the system message
            model_name (str): the model name
            remote_address (str): the remote address of the agent. Default is "http://localhost:8001/v1"
            api_key (str): the API key. Default is "sk-no-key-required"'''
        
        super().__init__(system_message, model_name, remote_address)
        self._api_key = api_key
        self._openai_config = openai_config
    
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return (f"{self.__class__.__name__}(system_message={self.system_message}, model_name={self.model_name},"
                f"remote_address={self.remote_address}, api_key={self.api_key})")
    
    def __getstate__(self) -> object:
        '''Return the state of the agent. Removing the instance variable client to avoid it is serialized/deserialized by pyyaml.'''
        state = super().__getstate__()
        if 'client' in state.keys():
            del state['client']
        return state 
    
    def connect(self):
        '''Connect to the remote machine.'''
        print(f"Connecting to WiseAgentLLM on remote machine at {self.remote_address} with API key {self.api_key}")
        self.client = openai.OpenAI(base_url=self.remote_address, 
                api_key=self.api_key)
    
   
    def process_single_prompt(self, prompt):
        '''Process a single prompt. This method is implemented from superclass WiseAgentLLM.
        The single prompt is processed and the result is returned, all the context and state is maintained locally in the method

        Args:
            prompt (str): the prompt to process'''
        print(f"Executing WiseAgentLLM on remote machine at {self.remote_address}")
        if (self.client is None):
            self.connect()
        messages = []
        messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model_name,
            #tools=tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
            **self.openai_config
            )
        return response.choices[0].message
   
    def process_chat_completion(self, 
                                messages: Iterable[ChatCompletionMessageParam], 
                                tools: Iterable[ChatCompletionToolParam]) -> ChatCompletion:
        '''Process a chat completion. This method is implemented from superclass WiseAgentLLM.
        The context and state is passed in input and returned as part of the output.
        Deal with the messages and tools is responsibility of the caller.

        Args:
            messages (Iterable[ChatCompletionMessageParam]): the messages to process
            tools (Iterable[ChatCompletionToolParam]): the tools to use
        
        Returns:
                ChatCompletion: the chat completion result'''
        print(f"Executing WiseAgentLLM on remote machine at {self.remote_address}")
        if (self.client is None):
            self.connect()
        #messages = []
        #messages.append({"role": "system", "content": self.system_message})
        #messages.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model_name,
            tools=tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
            **self.openai_config
            )
        return response
        
    @property
    def api_key(self):
        '''Get the API key.'''
        return self._api_key
    @property
    def openai_config(self):
        '''Get the OpenAI configuration.'''
        return self._openai_config

        