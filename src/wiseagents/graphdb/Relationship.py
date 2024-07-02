from typing import Optional

from pydantic import BaseModel, Field

from wiseagents.graphdb.Entity import Entity


class Relationship(BaseModel):
    """
    A relationship (edge) in a knowledge graph.

    Attributes:
        label (str): a description of the relationship
        source (Entity): the source entity
        target (Entity): the target entity
        metadata (Optional[dict]): optional information about the relationship
    """
    label: str
    source: Entity
    target: Entity
    metadata: Optional[dict] = Field(default_factory=dict)
