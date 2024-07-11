import uuid
from typing import Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """
    A document is a chunk of text.

    content (str): the string that makes up the chunk of text
    id (str): the optional id associated with the chunk of text
    metadata (Optional[dict]): optional information about the chunk of text
    """
    content: str
    id: Optional[str] = str(uuid.uuid4())
    metadata: Optional[dict] = Field(default_factory=dict)
