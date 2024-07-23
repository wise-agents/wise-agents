from abc import abstractmethod
from typing import Callable, Optional, List

from langchain_community.graphs import Neo4jGraph
from langchain_community.graphs.graph_document import (GraphDocument as LangChainGraphDocument,
                                                       Relationship as LangChainRelationship, Node)
from langchain_community.vectorstores import Neo4jVector
from langchain_core.documents import Document as LangChainDocument
from langchain_huggingface import HuggingFaceEmbeddings
from wiseagents.vectordb import Document

from .wise_agent_graph_db import Entity, Source, GraphDocument, Relationship, WiseAgentGraphDB
from ..constants import DEFAULT_EMBEDDING_MODEL_NAME


class LangChainWiseAgentGraphDB(WiseAgentGraphDB):

    def __init__(self, embedding_model_name: Optional[str] = DEFAULT_EMBEDDING_MODEL_NAME):
        self._embedding_model_name = embedding_model_name
        self._embedding_function = HuggingFaceEmbeddings(model_name=self.embedding_model_name)

    @property
    def embedding_model_name(self):
        return self._embedding_model_name

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

    @abstractmethod
    def get_schema(self) -> str:
        ...

    @abstractmethod
    def refresh_schema(self):
        ...

    @abstractmethod
    def query(self, query: str, params: Optional[dict] = None):
        ...

    @abstractmethod
    def insert_entity(self, entity: Entity, source: Source):
        ...

    @abstractmethod
    def insert_relationship(self, relationship: Relationship, source: Source):
        ...

    @abstractmethod
    def insert_graph_documents(self, graph_documents: List[GraphDocument]):
        ...

    @abstractmethod
    def create_vector_db_from_graph_db(self, retrieval_query: str = ""):
        ...


class Neo4jLangChainWiseAgentGraphDB(LangChainWiseAgentGraphDB):
    yaml_tag = u'!Neo4jLangChainWiseAgentGraphDB'

    def __init__(self, properties: List[str], collection_name: str, url: Optional[str] = None,
                 refresh_graph_schema: Optional[bool] = True,
                 embedding_model_name: Optional[str] = DEFAULT_EMBEDDING_MODEL_NAME,
                 entity_label: Optional[str] = "entity"):
        """Neo4jGraph will obtain the username, password, and database name to be used from
        the NEO4J_USERNAME, NEO4J_PASSWORD, and NEO4J_DATABASE environment variables."""
        super().__init__(embedding_model_name)
        self._properties = properties
        self._collection_name = collection_name
        self._url = url
        self._refresh_graph_schema = refresh_graph_schema
        self._entity_label = entity_label
        self._neo4j_graph_db = None
        self._neo4j_vector_db = None

    def __repr__(self):
        """Return a string representation of the graph DB."""
        return (f"{self.__class__.__name__}(properties={self.properties}, url={self.url}, refresh_schema={self.refresh_graph_schema},"
                f"embedding_model_name={self.embedding_model_name}, collection_name={self.collection_name},"
                f"entity_label={self._entity_label}")

    def __getstate__(self) -> object:
        """Return the state of the graph DB. Removing the instance variable neo4j_graph_db to avoid it being serialized/deserialized by pyyaml."""
        state = self.__dict__.copy()
        del state['_neo4j_graph_db']
        del state['_neo4j_vector_db']
        del state['_embedding_function']
        return state

    @classmethod
    def from_yaml(cls, loader, node):
        data = loader.construct_mapping(node, deep=True)
        url = data.get('_url', None)
        refresh_graph_schema = data.get('_refresh_graph_schema', True)
        embedding_model_name = data.get('_embedding_model_name', DEFAULT_EMBEDDING_MODEL_NAME)
        entity_label = data.get('_entity_label', "entity")
        return cls(properties=data.get('_properties'), collection_name=data.get('_collection_name'),
                   url=url, refresh_graph_schema=refresh_graph_schema, embedding_model_name=embedding_model_name,
                   entity_label=entity_label)

    @property
    def properties(self):
        return self._properties

    @property
    def collection_name(self):
        return self._collection_name

    @property
    def entity_label(self):
        return self._entity_label

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

    def create_vector_db_from_graph_db(self, retrieval_query: str = ""):
        self.connect()
        self._neo4j_vector_db = Neo4jVector.from_existing_graph(embedding=self._embedding_function,
                                                                node_label=self.entity_label,
                                                                embedding_node_property="embedding",
                                                                text_node_properties=self.properties,
                                                                url=self.url,
                                                                index_name=self.collection_name,
                                                                retrieval_query=retrieval_query)

    def query_with_embeddings(self, query: str, k: int, retrieval_query: str = "") -> List[Document]:
        if self._neo4j_vector_db is None:
            self.create_vector_db_from_graph_db(retrieval_query=retrieval_query)
        return [Document(content=doc.page_content, metadata=doc.metadata)
                for doc in self._neo4j_vector_db.similarity_search(query, k)]

    def delete_vector_db(self):
        if self._neo4j_vector_db is not None:
            self._neo4j_vector_db.delete_index()
            self._neo4j_vector_db = None

    def close(self):
        """
        Close the neo4j driver.
        """
        if self._neo4j_graph_db is not None:
            self._neo4j_graph_db._driver.close()
        if self._neo4j_vector_db is not None:
            self._neo4j_vector_db._driver.close()

