from typing import Callable, Optional, List

from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import (GraphDocument as LangChainGraphDocument,
                                                       Relationship as LangChainRelationship, Node)
from langchain_community.vectorstores import Neo4jVector
from langchain_core.documents import Document as LangChainDocument
from langchain_huggingface import HuggingFaceEmbeddings
from wiseagents.vectordb import Document

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

    def __init__(self, url: Optional[str] = None, refresh_graph_schema: Optional[bool] = True,
                 embedding_function: Optional[Callable] = None):
        """Neo4jGraph will obtain the username, password, and database name to be used from
        the NEO4J_USERNAME, NEO4J_PASSWORD, and NEO4J_DATABASE environment variables."""
        self._url = url
        self._refresh_graph_schema = refresh_graph_schema
        self._neo4j_graph_db = None
        self._neo4j_vector_db = None
        if embedding_function is None:
            self._embedding_function = self.get_default_embeddings()

    def __repr__(self):
        """Return a string representation of the graph DB."""
        return f"{self.__class__.__name__}(url={self.url}, refresh_schema={self.refresh_graph_schema})"

    def __getstate__(self) -> object:
        """Return the state of the graph DB. Removing the instance variable neo4j_graph_db to avoid it being serialized/deserialized by pyyaml."""
        state = self.__dict__.copy()
        del state['_neo4j_graph_db']
        del state['_neo4j_vector_db']
        return state

    @property
    def url(self):
        return self._url

    @property
    def refresh_graph_schema(self):
        return self._refresh_graph_schema

    def connect(self):
        if self._neo4j_graph_db is None:
            self._neo4j_graph_db = Neo4jGraph(url=self.url, refresh_schema=self.refresh_graph_schema)

    def get_schema(self) -> str:
        self.connect()
        return self._neo4j_graph_db.get_schema

    def refresh_schema(self):
        self.connect()
        self._neo4j_graph_db.refresh_schema()

    def query(self, query: str, params: Optional[dict] = None):
        self.connect()
        return self._neo4j_graph_db.query(query=query, params=params)

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
        self._neo4j_graph_db.add_graph_documents([self.convert_to_lang_chain_graph_document(graph_document)
                                                  for graph_document in graph_documents])

    def create_vector_db_from_graph_db(self, properties: List[str], collection_name: str,
                                       entity_label: Optional[str] = "entity"):
        self.connect()
        self._neo4j_vector_db = Neo4jVector.from_existing_graph(embedding=self._embedding_function,
                                                                node_label=entity_label,
                                                                embedding_node_property="embedding",
                                                                text_node_properties=properties,
                                                                url=self.url,
                                                                index_name=collection_name)

    def query_vector_db(self, query: str, k: int) -> List[Document]:
        if self._neo4j_vector_db is None:
            raise ValueError("Vector DB is not initialized. Please call create_vector_db_from_graph_db() first.")
        return [Document(content=doc.page_content, metadata=doc.metadata)
                for doc in self._neo4j_vector_db.similarity_search(query, k)]

    def close(self):
        """
        Close the neo4j driver.
        """
        if self._neo4j_graph_db is not None:
            self._neo4j_graph_db._driver.close()
        if self._neo4j_vector_db is not None:
            self._neo4j_vector_db._driver.close()

    @staticmethod
    def get_default_embeddings():
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
