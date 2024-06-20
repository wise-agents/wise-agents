from abc import abstractmethod
class WiseAgentLLM:
    def __init__(self, system_message, model_name):
        super().__init__()
        self._system_message = system_message
        self._model_name = model_name
        
    @property  
    def system_message(self):
        return self._system_message

    @property
    def model_name(self):
        return self._model_name     

    @abstractmethod
    def process(self, message):
        ...