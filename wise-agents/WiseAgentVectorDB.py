from abc import ABC, abstractmethod
from typing import Callable, Optional, Any, List, TypedDict, Union


class Document(TypedDict):
    """
    A document is a chunk of text.

    content (str): the string that makes up the chunk of text
    id (Union[str, int]): the id associated with the chunk of text
    metadata (Optional[dict]): optional information about the chunk of text
    """
    content: str
    id: Union[str, int]
    metadata: Optional[dict]


class WiseAgentVectorDB(ABC):

    @abstractmethod
    def create_collection(self, collection_name: str, embedding_function: Optional[Callable] = None,
                          metadata: Optional[dict] = None) -> Any:
        """
        Create a collection for the vector DB. If the collection with the specified name already exists
        in the vectorDB, it will be overwritten.

        Args:
            collection_name (str): the name of the collection
            embedding_function (Callable): the optional embedding function to use for the collection (or None to use
            the vector DB's default embedding function)
            metadata (dict): the optional metadata associated with the collection

        Returns:
            Any: the collection
        """
        ...

    @abstractmethod
    def get_or_create_collection(self, collection_name: str, embedding_function: Optional[Callable] = None,
                                 metadata: Optional[dict] = None) -> Any:
        """
        Get or create a collection for the vector DB. If the collection with the specified name already exists
        in the vector DB, it will be returned.

        Args:
            collection_name (str): the name of the collection
            embedding_function (Callable): the optional embedding function to use for the collection (or None to use
            the vector DB's default embedding function)
            metadata (dict): the optional metadata associated with the collection

            Returns:
                Any: the collection
        """
        ...

    @abstractmethod
    def get_collection(self, collection_name: str) -> Any:
        """
        Get the collection with the specified name from the vector DB.

        Args:
            collection_name (str): the name of the collection to retrieve

        Returns:
            Any: the collection
        """
        ...

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """
        Delete the collection with the specified name from the vector DB.

        Args:
            collection_name (str): the name of the collection to delete
        """
        ...

    @abstractmethod
    def insert_documents(self, documents: List[Document], collection_name: str):
        """
        Insert the given documents into the specified collection in the vector DB.

        Args:
            documents (List[Document]): the documents to be inserted into the specified collection
            collection_name (str): the name of the collection in the vector DB to insert the documents into
        """
        ...

    @abstractmethod
    def insert_or_update_documents(self, documents: List[Document], collection_name: str):
        """
        Insert the given documents into the specified collection in the vector DB, updating any
        documents that already exist in the collection.

        Args:
            documents (List[Document]): the documents to be inserted into the specified collection
            collection_name (str): the name of the collection in the vector DB to insert the documents into
        """
        ...

    @abstractmethod
    def delete_documents(self, ids: List[Union[str, int]], collection_name: str):
        """
        Delete documents from the specified collection in the vector DB.

        Args:
            ids (List[Union[str, int]]): the list of document IDs to be deleted
            collection_name (str): the name of the collection in the vector DB to delete the documents from
        """
        ...

    @abstractmethod
    def query(self, queries: List[str], collection_name: str) -> List[List[Document]]:
        """
        Retrieve documents from the specified collection in the vector DB using the given queries.

        Args:
            queries (List[str]): the list of queries where each query is a string
            collection_name (str): the name of the collection in the vector DB to query

        Returns:
            List[List[Document]]: the list containing a list of documents that were
            retrieved for each query
        """
        ...
