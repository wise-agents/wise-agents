from typing import Optional
from pydantic import BaseModel

import WiseAgentMessageType


class WiseAgentMessage(BaseModel):
    sender: Optional[str] = None
    type: WiseAgentMessageType
    """
    TODO
    """


