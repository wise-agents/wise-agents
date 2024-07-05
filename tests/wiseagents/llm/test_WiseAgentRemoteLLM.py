from wiseagents.llm.lang_chain_wise_agent_remote_LLM import LangChainWiseAgentRemoteLLM
from wiseagents.llm.openai_API_wise_agent_LLM import OpenaiAPIWiseAgentLLM

  
def test_langchain():
        agent = LangChainWiseAgentRemoteLLM("Answer my greeting saying Hello and my name", "Phi-3-mini-4k-instruct-q4.gguf","http://localhost:8001/v1")
        response = agent.process("Hello my name is Stefano")
        assert "Stefano" in response.content
        

def test_openai():
        agent = OpenaiAPIWiseAgentLLM("Answer my greeting saying Hello and my name", "Phi-3-mini-4k-instruct-q4.gguf","http://localhost:8001/v1")
        response = agent.process("Hello my name is Stefano")
        assert "Stefano" in response.content