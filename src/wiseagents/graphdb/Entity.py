from typing import Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """
    An entity (node) in a knowledge graph.

    Attributes:
        id (str): the unique id for the entity
        label (Optional[str]): an optional label for the entity
        metadata (Optional[dict]): optional information about the entity
    """
    id: str
    label: Optional[str] = "entity"
    metadata: Optional[dict] = Field(default_factory=dict)
