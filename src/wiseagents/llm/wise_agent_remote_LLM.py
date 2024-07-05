from wiseagents.llm.wise_agent_LLM import WiseAgentLLM
from abc import abstractmethod


class WiseAgentRemoteLLM(WiseAgentLLM):
    """Extend WiseAgentLLM to support remote execution of WiseAgentLLM on a remote machine."""
    yaml_tag = u'!WiseAgentRemoteLLM'    
    
    def __init__(self, system_message, model_name, remote_address):
        super().__init__(system_message, model_name)
        self._remote_address = remote_address
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(system_message={self.system_message}, model_name={self.model_name}, remote_address={self.remote_address})"
    
    @property
    def remote_address(self):
        return self._remote_address
    
    @abstractmethod
    def process(self, message):
        ...
    