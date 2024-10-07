from abc import abstractmethod
from typing import Iterable, Optional

import yaml
from openai.types.chat import ChatCompletionMessageParam, ChatCompletion, ChatCompletionToolParam

from wiseagents import enforce_no_abstract_class_instances
from wiseagents.yaml import WiseAgentsYAMLObject


class WiseAgentLLM(WiseAgentsYAMLObject):
    """Abstract class to define the interface for a WiseAgentLLM."""
    def __init__(self, model_name, system_message: Optional[str] = None):
        '''Initialize the agent.

        Args:
            model_name (str): the model name
            system_message (Optional[str]): the optional system message
        '''
        super().__init__()
        enforce_no_abstract_class_instances(self.__class__, WiseAgentLLM)
        self._system_message = system_message
        self._model_name = model_name
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(system_message={self.system_message}, model_name={self.model_name})"    
    
    @property  
    def system_message(self) -> Optional[str]:
        '''Get the system message or None if no system message has been defined.'''
        return self._system_message

    @property
    def model_name(self):
        '''Get the model name.'''
        return self._model_name     

    @abstractmethod
    def process_single_prompt(self, prompt):
        '''Process a single prompt. This method should be implemented by subclasses.
        The single prompt is processed and the result is returned, all the context and state is maintained locally in the method

        Args:
            prompt (str): the prompt to process'''
        
        ...
    
    @abstractmethod
    def process_chat_completion(self, 
                                messages: Iterable[ChatCompletionMessageParam], 
                                tools: Iterable[ChatCompletionToolParam]) -> ChatCompletion:
        '''Process a chat completion. This method should be implemented by subclasses.
        The context and state is passed in input and returned as part of the output.
        Deal with the messages and tools is responsibility of the caller.

        Args:
            messages (Iterable[ChatCompletionMessageParam]): the messages to process
            tools (Iterable[ChatCompletionToolParam]): the tools to use
        
        Returns:
                ChatCompletion: the chat completion result'''
        ...