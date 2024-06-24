from typing import List

from pydantic import BaseModel
from wiseagents.graphdb.Entity import Entity
from wiseagents.graphdb.Relationship import Relationship


class GraphDocument(BaseModel):
    """
    A graph document is a collection of entities and relationships that are part of a knowledge graph.

    Attributes:
        entities (List[Entity]): the entities in the graph document
        relationships (List[Relationship]): the relationships in the graph document
    """
    entities: List[Entity]
    relationships: List[Relationship]
