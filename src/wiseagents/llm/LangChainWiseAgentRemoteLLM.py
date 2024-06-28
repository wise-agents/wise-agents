from wiseagents.llm.WiseAgentRemoteLLM import WiseAgentRemoteLLM
import requests
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.callbacks import StdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory


class LangChainWiseAgentRemoteLLM(WiseAgentRemoteLLM):
      
    chain = None
    yaml_tag = u'!LangChainWiseAgentRemoteLLM'    
    
    
    def __init__(self, system_message, model_name, remote_address = "http://localhost:8001/v1"):
        super().__init__(system_message, model_name, remote_address)
        self.chain = None
    
    
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(system_message={self.system_message}, model_name={self.model_name}, remote_address={self.remote_address})"
    
    def __getstate__(self) -> object:
        '''Return the state of the agent. Removing the instance variable chain to avoid it is serialized/deserialized by pyyaml.'''
        state = self.__dict__.copy()
        del state['chain']
        return state 
    
    def connect(self):
        llm = ChatOpenAI(base_url=self.remote_address, 
            api_key="sk-no-key-required",
            model=self.model_name,
            streaming=True)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            MessagesPlaceholder("history"),
            ("human", "{message}")
        ])          
        self.chain = prompt | llm
    
    @property    
    def memory(self) -> ConversationBufferWindowMemory:
        memory = ConversationBufferWindowMemory(return_messages=True,k=3)
        return memory

   
    def process(self, message):
        print(f"Executing WiseAgentLLM on remote machine at {WiseAgentRemoteLLM.remote_address}")
        buffer = self.memory
        if (self.chain is None):
            self.connect()
        response = self.chain.invoke({
                "history": buffer.buffer_as_messages,
                "message": message
                })
        return response
        
        
        

        