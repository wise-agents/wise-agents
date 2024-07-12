import pytest
from wiseagents.llm.lang_chain_wise_agent_remote_LLM import LangChainWiseAgentRemoteLLM

  
def test_method1():
        agent = LangChainWiseAgentRemoteLLM("Answer my greeting saying Hello and my name", "Phi-3-mini-4k-instruct-q4.gguf","http://localhost:8001/v1")
        response = agent.process("Hello my name is Stefano")
        assert response.content.__len__() > 0