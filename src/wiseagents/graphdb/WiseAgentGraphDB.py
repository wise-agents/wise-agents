from abc import ABC, abstractmethod
from typing import Optional, Any, List

from wiseagents.graphdb.Entity import Entity
from wiseagents.graphdb.GraphDocument import GraphDocument
from wiseagents.graphdb.Relationship import Relationship


class WiseAgentGraphDB(ABC):

    @abstractmethod
    def get_schema(self, refresh: bool = False) -> str:
        """
        Get the schema of the graph DB.

        Args:
            refresh (bool): True if the schema should be refreshed, False otherwise

        Returns:
            str: the schema of the graph DB
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
    def insert_entity(self, entity: Entity):
        """
        Insert an entity into the graph DB.

        Args:
            entity (Entity): the entity to insert
        """
        ...

    @abstractmethod
    def insert_relationship(self, relationship: Relationship):
        """
        Insert a relationship into the graph DB.

        Args:
            relationship (Relationship): the relationship to insert
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

