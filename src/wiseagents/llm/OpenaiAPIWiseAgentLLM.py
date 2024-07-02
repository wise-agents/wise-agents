from wiseagents.llm.WiseAgentRemoteLLM import WiseAgentRemoteLLM
import requests
import openai

class OpenaiAPIWiseAgentLLM(WiseAgentRemoteLLM):
    
    client = None
    yaml_tag = u'!OpenaiAPIWiseAgentLLM'    
    
    
    def __init__(self, system_message, model_name, remote_address = "http://localhost:8001/v1"):
        super().__init__(system_message, model_name, remote_address)
        self.chain = None
    
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(system_message={self.system_message}, model_name={self.model_name}, remote_address={self.remote_address})"
    
    def __getstate__(self) -> object:
        '''Return the state of the agent. Removing the instance variable chain to avoid it is serialized/deserialized by pyyaml.'''
        state = self.__dict__.copy()
        del state['client']
        return state 
    
    def connect(self):
        self.client = openai.OpenAI(base_url=self.remote_address, 
                api_key="sk-no-key-required")
    
   
    def process(self, message):
        print(f"Executing WiseAgentLLM on remote machine at {WiseAgentRemoteLLM.remote_address}")
        if (self.client is None):
            self.connect()
        messages = []
        messages.append({"role": "system", "content": self.system_message})
        messages.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model_name,
            #tools=tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
            )
        return response.choices[0].message
        
    
        

        