import json
import os
from typing import List, Optional

from openai.types.chat import ChatCompletionMessageParam


class AbstractClassError(Exception):
    pass


def enforce_no_abstract_class_instances(cls: type, check: type):
    """
    Check if a class has abstract methods.

    Args:
        cls (type): The class to check.
        check (type): cls should not be this

    :raises NotImplementedError: If the class has abstract methods.
    """
    for key, value in cls.__dict__.items():
        if cls is check:
            raise AbstractClassError(f"Class {cls.__name} is an abstract class and cannot be instantiated.")


def log_messages_exchanged(messages: List[ChatCompletionMessageParam], agent_name: str,
                           context_name: str, dir_path: Optional[str] = './log'):
    """
    Log the messages exchanged in a conversation to the given file.

    Args:
        messages: the messages to be logged
        agent_name: the name of the agent involved in this conversation with an LLM
        context_name: the name of the context in which the conversation took place
        dir_path: the directory path to output the log file to, defaults to './log'
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    with open(f'{dir_path}/messages-{agent_name}-{context_name}.md', 'w') as file:
        message : ChatCompletionMessageParam
        for message  in messages:
            file.write(f"## {message.get('role')}\n {message.get('content')}\n\n\n")
            #file.write(f"{message}\n\n\n")
    with open(f'{dir_path}/messages-{agent_name}-{context_name}.log', 'w') as file:
        json.dump(messages, file, indent=2)
    print(f"[{agent_name}] Logged messages to {dir_path}/messages-{agent_name}-{context_name}.log for the current request")
