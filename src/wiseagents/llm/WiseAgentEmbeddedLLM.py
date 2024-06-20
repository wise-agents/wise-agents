import WiseAgentLLM

class WiseAgentEmbeddedLLM(WiseAgentLLM):
    """Extends WiseAgentLLM to support local execution of WiseAgentLLM on the local machine."""
        
    def __init__(self):
        super().__init__()
    
    def process(self):
        # Add code here to execute the WiseAgentLLM on the local machine
        pass