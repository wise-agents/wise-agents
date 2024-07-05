from typing import Optional, List

from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import (GraphDocument as LangChainGraphDocument,
                                                       Relationship as LangChainRelationship, Node)
from langchain_core.documents import Document as LangChainDocument

from .wise_agent_graph_db import Entity, Source, GraphDocument, Relationship, WiseAgentGraphDB


class LangChainWiseAgentGraphDB(WiseAgentGraphDB):

    def convert_to_lang_chain_node(self, entity: Entity) -> Node:
        return Node(id=entity.id, type=entity.label, properties=entity.metadata)

    def convert_to_lang_chain_relationship(self, relationship: Relationship) -> LangChainRelationship:
        return LangChainRelationship(source=self.convert_to_lang_chain_node(relationship.source),
                                     target=self.convert_to_lang_chain_node(relationship.target),
                                     type=relationship.label,
                                     properties=relationship.metadata)

    def convert_to_lang_chain_graph_document(self, graph_document: GraphDocument) -> LangChainGraphDocument:
        return LangChainGraphDocument(nodes=[self.convert_to_lang_chain_node(entity)
                                             for entity in graph_document.entities],
                                      relationships=[self.convert_to_lang_chain_relationship(relationship)
                                                     for relationship in graph_document.relationships],
                                      source=self.convert_to_lang_chain_document(graph_document.source))

    def convert_to_lang_chain_document(self, source: Source) -> LangChainDocument:
        return LangChainDocument(id=source.id, page_content=source.content, metadata=source.metadata)


class Neo4jLangChainWiseAgentGraphDB(LangChainWiseAgentGraphDB):
    yaml_tag = u'!Neo4jLangChainWiseAgentGraphDB'

    def __init__(self, url: Optional[str] = None, refresh_graph_schema: Optional[bool] = True):
        """Neo4jGraph will obtain the username, password, and database name to be used from
        the NEO4J_USERNAME, NEO4J_PASSWORD, and NEO4J_DATABASE environment variables."""
        self._url = url
        self._refresh_graph_schema = refresh_graph_schema
        self.neo4j_graph_db = None

    def __repr__(self):
        """Return a string representation of the graph DB."""
        return f"{self.__class__.__name__}(url={self.url}, refresh_schema={self.refresh_graph_schema})"

    def __getstate__(self) -> object:
        """Return the state of the graph DB. Removing the instance variable neo4j_graph_db to avoid it being serialized/deserialized by pyyaml."""
        state = self.__dict__.copy()
        del state['neo4j_graph_db']
        return state

    @property
    def url(self):
        return self._url

    @property
    def refresh_graph_schema(self):
        return self._refresh_graph_schema

    def connect(self):
        if self.neo4j_graph_db is None:
            self.neo4j_graph_db = Neo4jGraph(url=self.url, refresh_schema=self.refresh_graph_schema)

    def get_schema(self) -> str:
        self.connect()
        return self.neo4j_graph_db.get_schema

    def refresh_schema(self):
        self.connect()
        self.neo4j_graph_db.refresh_schema()

    def query(self, query: str, params: Optional[dict] = None):
        self.connect()
        return self.neo4j_graph_db.query(query=query, params=params)

    def insert_entity(self, entity: Entity, source: Source):
        self.connect()
        self.insert_graph_documents([GraphDocument(entities=[entity],
                                                   relationships=[],
                                                   source=source)])

    def insert_relationship(self, relationship: Relationship, source: Source):
        self.connect()
        self.insert_graph_documents([GraphDocument(entities=[],
                                                   relationships=[relationship],
                                                   source=source)])

    def insert_graph_documents(self, graph_documents: List[GraphDocument]):
        self.connect()
        self.neo4j_graph_db.add_graph_documents([self.convert_to_lang_chain_graph_document(graph_document)
                                                 for graph_document in graph_documents])

    def close(self):
        """
        Close the neo4j driver.
        """
        if self.neo4j_graph_db is not None:
            self.neo4j_graph_db._driver.close()
