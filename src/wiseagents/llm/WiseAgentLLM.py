from abc import abstractmethod
import yaml
class WiseAgentLLM(yaml.YAMLObject):
    """Abstract class to define the interface for a WiseAgentLLM."""
    yaml_tag = u'!WiseAgentLLM'    
    def __init__(self, system_message, model_name):
        super().__init__()
        self._system_message = system_message
        self._model_name = model_name
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(system_message={self.system_message}, model_name={self.model_name})"    
    
    @property  
    def system_message(self):
        return self._system_message

    @property
    def model_name(self):
        return self._model_name     

    @abstractmethod
    def process(self, message):
        ...