from typing import Union, Optional

from pydantic import BaseModel


class Entity(BaseModel):
    """
    An entity (node) in a knowledge graph.

    Attributes:
        id (Union[str, int]): the unique id for the entity
        label (str): a description of the entity
        metadata (Optional[dict]): optional information about the entity
    """
    id: Union[str, int]
    label: str
    metadata: Optional[dict] = None
