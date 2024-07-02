import uuid
from typing import Optional

from pydantic import BaseModel


class Source(BaseModel):
    """
    Information about a source from which entities and relationships have been derived from.

    Attributes:
        content (str): the content of the source
        id (str): the optional id associated with the source
        metadata (Optional[dict]): optional information about the source
    """
    content: str
    id: Optional[str] = str(uuid.uuid4())
    metadata: Optional[dict] = {}

