from wiseagents import WiseAgentRegistry
from wiseagents.llm import OpenaiAPIWiseAgentLLM
import pytest


@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    WiseAgentRegistry.clear_agents()
    WiseAgentRegistry.clear_contexts()

@pytest.mark.needsllm
def test_openai():
        agent = OpenaiAPIWiseAgentLLM("Answer my greeting saying Hello and my name", "Phi-3-mini-4k-instruct-q4.gguf","http://localhost:8001/v1")
        response = agent.process_single_prompt("Hello my name is Stefano")
        assert "Stefano" in response.content