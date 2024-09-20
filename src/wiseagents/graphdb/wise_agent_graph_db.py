import uuid
from abc import abstractmethod
from typing import Optional, Any, List

import yaml
from pydantic import BaseModel, Field

from wiseagents import enforce_no_abstract_class_instances
from wiseagents.yaml import WiseAgentsLoader


class Entity(BaseModel):
    """
    An entity (node) in a knowledge graph.

    Attributes:
        id (Optional[str]): the unique id for the entity
        label (Optional[str]): an optional label for the entity
        metadata (Optional[dict]): optional information about the entity
    """
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    label: Optional[str] = "entity"
    metadata: Optional[dict] = Field(default_factory=dict)


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


class Source(BaseModel):
    """
    Information about a source from which entities and relationships have been derived from.

    Attributes:
        content (str): the content of the source
        id (str): the optional id associated with the source
        metadata (Optional[dict]): optional information about the source
    """
    content: str
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[dict] = {}


class GraphDocument(BaseModel):
    """
    A graph document is a collection of entities and relationships that are part of a knowledge graph.

    Attributes:
        entities (List[Entity]): the entities in the graph document
        relationships (List[Relationship]): the relationships in the graph document
        source (Source): the source that contains the entities and relationships
    """
    entities: List[Entity]
    relationships: List[Relationship]
    source: Source


class WiseAgentGraphDB(yaml.YAMLObject):
    """Abstract class to define the interface for a WiseAgentGraphDB."""

    yaml_loader = WiseAgentsLoader

    def __init__(self):
        enforce_no_abstract_class_instances(self.__class__, WiseAgentGraphDB)

    @abstractmethod
    def get_schema(self) -> str:
        """
        Get the schema of the graph DB.

        Returns:
            str: the schema of the graph DB
        """
        ...

    @abstractmethod
    def refresh_schema(self):
        """
        Refresh the schema of the graph DB.
        """
        ...

    @abstractmethod
    def query(self, query: str, params: Optional[dict] = None) -> Any:
        """
        Query the graph DB.


        Args:
            query (str): the query to execute
            params (dict): the optional parameters for the query

        Returns:
            Any: the result of the query
        """
        ...

    @abstractmethod
    def insert_entity(self, entity: Entity, source: Source):
        """
        Insert an entity into the graph DB.


        Args:
            entity (Entity): the entity to insert
            source (Source): information about the source from which the entity has been derived from
        """
        ...

    @abstractmethod
    def insert_relationship(self, relationship: Relationship, source: Source):
        """
        Insert a relationship into the graph DB.


        Args:
            relationship (Relationship): the relationship to insert
            source (Source): information about the source from which the relationship has been derived from
        """
        ...

    @abstractmethod
    def insert_graph_documents(self, graph_documents: List[GraphDocument]):
        """
        Insert a list of graph documents into the graph DB.


        Args:
            graph_documents (List[GraphDocuments]): the graph documents to insert
        """
        ...
