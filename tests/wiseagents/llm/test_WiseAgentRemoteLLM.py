import pytest

from wiseagents.llm import OpenaiAPIWiseAgentLLM
from tests.wiseagents import assert_standard_variables_set

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    assert_standard_variables_set()
    yield
    
    

@pytest.mark.needsllm
def test_openai():
        agent = OpenaiAPIWiseAgentLLM("Answer my greeting saying Hello and my name", model_name="llama3.1",
                                            remote_address="http://localhost:11434/v1")
        response = agent.process_single_prompt("Hello my name is Stefano")
        assert "Stefano" in response.content

