from typing import Optional, List, Callable

from langchain_core.documents import Document as LangChainDocument
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from .wise_agent_vector_db import Document
from .wise_agent_vector_db import WiseAgentVectorDB


class LangChainWiseAgentVectorDB(WiseAgentVectorDB):

    def __init__(self, embedding_model_name: Optional[str] = None):
        self._embedding_model_name = embedding_model_name
        if self._embedding_model_name is None:
            # default model will be used
            self._embedding_function = HuggingFaceEmbeddings()
        else:
            self._embedding_function = HuggingFaceEmbeddings(model_name=embedding_model_name)

    def convert_from_lang_chain_documents(self, documents: List[LangChainDocument]) -> List[Document]:
        return [Document(content=document.page_content, metadata=document.metadata) for document in documents]


class PGVectorLangChainWiseAgentVectorDB(LangChainWiseAgentVectorDB):
    yaml_tag = u'!PGVectorLangChainWiseAgentVectorDB'

    def __init__(self, connection_string: str, embedding_model_name: Optional[str] = None):
        super().__init__(embedding_model_name)
        self._connection_string = connection_string
        self._vector_dbs = {}

    def __repr__(self):
        """Return a string representation of the vector DB."""
        return (f"{self.__class__.__name__}(connection_string={self.connection_string},"
                f"embedding_model_name={self.embedding_model_name})")


    def __getstate__(self) -> object:
        """Return the state of the vector DB. Removing _vector_dbs and _embedding_function to avoid them being serialized/deserialized by pyyaml."""
        state = self.__dict__.copy()
        del state['_vector_dbs']
        del state['_embedding_function']
        return state

    @property
    def connection_string(self):
        return self._connection_string

    @property
    def embedding_model_name(self):
        return self._embedding_model_name

    def create_collection(self, collection_name: str, embedding_function: Optional[Callable] = None):
        if embedding_function is None:
            embedding_function = self._embedding_function
        if collection_name not in self._vector_dbs:
            self._vector_dbs[collection_name] = PGVector(embeddings=embedding_function,
                                                         collection_name=collection_name,
                                                         connection=self._connection_string)

    def delete_collection(self, collection_name: str):
        if collection_name in self._vector_dbs:
            self._vector_dbs[collection_name].delete_collection()
            del self._vector_dbs[collection_name]

    def insert_documents(self, documents: List[Document], collection_name: str):
        if collection_name not in self._vector_dbs:
            self.create_collection(collection_name)
        self._vector_dbs[collection_name].add_texts(texts=[doc.content for doc in documents],
                                                    ids=[doc.id for doc in documents],
                                                    metadatas=[doc.metadata for doc in documents])

    def insert_or_update_documents(self, documents: List[Document], collection_name: str):
        if collection_name not in self._vector_dbs:
            self.create_collection(collection_name)
        self.insert_documents(documents, collection_name)

    def delete_documents(self, document_ids: List[str], collection_name: str):
        if collection_name in self._vector_dbs:
            self._vector_dbs[collection_name].delete(ids=document_ids)

    def query(self, queries: List[str], collection_name: str, k: Optional[int] = 4) -> List[List[Document]]:
        if collection_name in self._vector_dbs:
            return [self.convert_from_lang_chain_documents(self._vector_dbs[collection_name].similarity_search(query, k))
                    for query in queries]

