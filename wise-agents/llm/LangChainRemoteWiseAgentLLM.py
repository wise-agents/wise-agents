from RemoteWiseAgentLLM import RemoteWiseAgentLLM
import requests
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.callbacks import StdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory


class LangChainRemoteWiseAgentLLM(RemoteWiseAgentLLM):
    
    chain = None
    
    def __init__(self, system_message, model_name, remote_address = "http://localhost:8001"):
        try:
            request_cpp = requests.get(f'{remote_address}/v1/models')
            if request_cpp.status_code == 200:
                self.server = "Llamacpp_Python"
                remote_address = f'{remote_address}/v1'
            print(f"Server {self.server} is Ready")
            super().__init__(system_message, model_name, remote_address)
            llm = ChatOpenAI(base_url=remote_address, 
                api_key="sk-no-key-required",
                model=self.model_name,
                streaming=True)

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                MessagesPlaceholder("history"),
                ("human", "{message}")
            ])          
            self.chain = prompt | llm
        except requests.exceptions.RequestException as e:
            print(f"Error: Could not connect to remote machine at {remote_address}")
            print(e)
            pass
    
    @property    
    def memory(self) -> ConversationBufferWindowMemory:
        memory = ConversationBufferWindowMemory(return_messages=True,k=3)
        return memory

   
    def process(self, message):
        print(f"Executing WiseAgentLLM on remote machine at {RemoteWiseAgentLLM.remote_address}")
        buffer = self.memory
        response = self.chain.invoke({
                "history": buffer.buffer_as_messages,
                "message": message
                })
        return response
        
        
        

        