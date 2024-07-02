from abc import abstractmethod
from typing import Optional, Any, List

from wiseagents.graphdb.Source import Source
from wiseagents.graphdb.Entity import Entity
from wiseagents.graphdb.GraphDocument import GraphDocument
from wiseagents.graphdb.Relationship import Relationship
import yaml


class WiseAgentGraphDB(yaml.YAMLObject):
    """Abstract class to define the interface for a WiseAgentGraphDB."""

    yaml_tag = u'!WiseAgentGraphDB'
    
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

