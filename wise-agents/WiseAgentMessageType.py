from enum import Enum, auto


class WiseAgentMessageType(Enum):
    ALERT = auto()
    QUERY = auto()
    RESPONSE = auto()
    ACTION_REQUEST = auto()
    HUMAN = auto()
