import pytest

from wiseagents.llm import OpenaiAPIWiseAgentLLM
from tests.wiseagents import assert_standard_variables_set, mock_open_ai_for_ci, mock_open_ai_chat_completion, find_in_user_messages


@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    assert_standard_variables_set()
    yield


def _mock_open_ai(*args, **kwargs):
    assert find_in_user_messages(kwargs["messages"], "Hello my name is Stefano"), \
        "Expected the message 'Hello my name is Stefano' to be in the messages"
    return mock_open_ai_chat_completion("Hello, Stefano!")


def test_openai(mocker):
    mock_open_ai_for_ci(mocker, _mock_open_ai)
    agent = OpenaiAPIWiseAgentLLM(system_message="Answer my greeting saying Hello and my name", model_name="llama3.1",
                                        remote_address="http://localhost:11434/v1")
    response = agent.process_single_prompt("Hello my name is Stefano")
    assert "Stefano" in response.content

