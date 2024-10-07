from abc import abstractmethod
from typing import Iterable, Optional

from openai.types.chat import ChatCompletion, ChatCompletionMessageParam, ChatCompletionToolParam

from wiseagents import enforce_no_abstract_class_instances
from wiseagents.llm.wise_agent_LLM import WiseAgentLLM


class WiseAgentRemoteLLM(WiseAgentLLM):
    """Extend WiseAgentLLM to support remote execution of WiseAgentLLM on a remote machine."""

    def __init__(self, model_name, remote_address, system_message: Optional[str] = None):
        super().__init__(model_name=model_name, system_message=system_message)
        enforce_no_abstract_class_instances(self.__class__, WiseAgentRemoteLLM)
        self._remote_address = remote_address
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(system_message={self.system_message}, model_name={self.model_name}, remote_address={self.remote_address})"
    
    @property
    def remote_address(self):
        '''Get the remote address.'''
        return self._remote_address
    
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