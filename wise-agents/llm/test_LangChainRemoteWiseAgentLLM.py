import pytest
from LangChainRemoteWiseAgentLLM import LangChainRemoteWiseAgentLLM

def test_method1():
        agent = LangChainRemoteWiseAgentLLM("Answer my greeting saying Hello and my name", "instructlab/granite-7b-lab-GGUF","http://localhost:8000")
        response = agent.process("Hello my name is Stefano")
        assert response.content.startswith(" Hi Stefano!")