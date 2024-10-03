import os

from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from pytest_mock import MockerFixture
from unittest.mock import Mock


def assert_standard_variables_set():
    assert_env_vars_set(
        "GROQ_API_KEY",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
        "NEO4J_DATABASE",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "STOMP_USER",
        "STOMP_PASSWORD")


def assert_env_vars_set(*var_names: str):
    for var_name in var_names:
        assert_env_var_set(var_name)


def assert_env_var_set(var_name: str) -> str:
    value = os.getenv(var_name)
    assert value, f"Need to set the {var_name} environment variable"
    return value


def mock_open_ai_for_ci(mocker: MockerFixture, fn: callable):
    """
    Mocks the Completions.create() method of the OpenAI API for CI testing. This avoids the need for an LLM.
    Args:
        mocker (pytest_mock.plugin.MockerFixture): the mocker fixture
        fn (function): Callback function to be called when the mocked method is called. The signature should be
            (*args, **kwargs)
    """
    # TODO Only do this if the MOCK_OPENAI_FOR_CI environment variable is set
    mocker.patch('openai.resources.chat.completions.Completions.create', side_effect=fn)


def mock_open_ai_chat_completion(*messages: str, extra: dict = None) -> ChatCompletion:
    """
    Mocks the Completions.create() method of the OpenAI API for CI testing. This avoids the need for an LLM.
    Args:
        fn (function): Callback function to be called when the mocked method is called. The signature should be
            (*args, **kwargs)
        extra (dict): Extra data to be added to the response
    """
    return mock_open_ai_chat_completion_with_mocker(None, *messages, extra=extra)


def mock_open_ai_chat_completion_with_mocker(mocker: MockerFixture | None, *messages: str, extra: dict = None) -> ChatCompletion:
    """
    Mocks the Completions.create() method of the OpenAI API for CI testing. This avoids the need for an LLM.
    Args:
        mocker (pytest_mock.plugin.MockerFixture): the mocker fixture
        fn (function): Callback function to be called when the mocked method is called. The signature should be
            (*args, **kwargs)
    """

    # TODO Keep this private for now.
    # This was an attempt to override the __setstate__ method of the ChatCompletionMessage mock object
    # in order to be able to do pickle.dumps() on it.
    # That part worked, but gave another error:
    #   {PicklingError}PicklingError('args[0] from __newobj__ args has the wrong class')
    #
    # Luckily we don't seem to be passing ChatCompletionMessages in to the picker, rather we are extracting
    # dicts with the important data.
    # In any case I decided to keep the code to override __setstate__ here in case we need it later.

    response = Mock(spec=ChatCompletion)
    response.choices = []
    for message in messages:

        completion_msg = Mock(spec=ChatCompletionMessage)
        if mocker:
            mocker.patch.object(completion_msg, "__getstate__", return_value={"content": message})

        completion_msg.content = message
        if extra:
            for key, value in extra.items():
                setattr(completion_msg, key, value)
        choice = Mock(spec=Choice)
        choice.message = completion_msg
        response.choices.append(choice)

    return response


def find_in_user_messages(messages: list[dict:str], search: str) -> bool:
    for msg in messages:
        if msg["role"] == "user" and msg["content"] == search:
            return True

    return False


def get_user_messages(messages: list[dict:str]) -> list[str]:
    return get_messages_for_role("user", messages)


def get_system_messages(messages: list[dict:str]) -> list[str]:
    return get_messages_for_role("system", messages)


def get_assistant_messages(messages: list[dict:str]) -> list[str]:
    return get_messages_for_role("assistant", messages)

def get_messages_for_role(role:str, messages: list[dict:str]) -> list[str]:
    role_messages = []
    for msg in messages:
        if msg["role"] == role:
            role_messages.append(msg["content"])

    return role_messages


#
# msg = mock_open_ai_chat_completion("Hello")
# print(msg)
# d = msg.__getstate__()
# print(msg.__getstate__())