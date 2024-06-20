from wiseagents.llm.WiseAgentLLM import WiseAgentLLM
from abc import abstractmethod

class WiseAgentRemoteLLM(WiseAgentLLM):
    """Extend WiseAgentLLM to support remote execution of WiseAgentLLM on a remote machine."""

    def __init__(self, system_message, model_name, remote_address):
        super().__init__(system_message, model_name)
        self._remote_address = remote_address
    
    @property
    def remote_address(self):
        return self._remote_address
    
    @abstractmethod
    def process(self, message):
        ...
    