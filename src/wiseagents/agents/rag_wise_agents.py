import json
import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from wiseagents import WiseAgent, WiseAgentCollaborationType, WiseAgentMessage, WiseAgentMetaData, WiseAgentTransport, \
    enforce_no_abstract_class_instances
from wiseagents.graphdb import WiseAgentGraphDB
from wiseagents.llm import WiseAgentLLM
from wiseagents.vectordb import Document, WiseAgentVectorDB
from openai.types.chat import ChatCompletionMessageParam

"""The default number of documents to retrieve during retrieval augmented generation (RAG)."""
DEFAULT_NUM_DOCUMENTS = 4

"""The default collection name to use during retrieval augmented generation (RAG)."""
DEFAULT_COLLECTION_NAME = "wise-agents-collection"

"""The default value for whether to include the sources of the documents that were consulted to produce the response
when using retrieval augmented generation (RAG)."""
DEFAULT_INCLUDE_SOURCES = False

"""The default number of verification questions to use when challenging the results retrieved from retrieval augmented
generation (RAG)."""
DEFAULT_NUM_VERIFICATION_QUESTIONS = 4

class RAGWiseAgent(WiseAgent):
    """
    This agent makes use of retrieval augmented generation (RAG) to answer questions.
    """
    yaml_tag = u'!wiseagents.agents.RAGWiseAgent'

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        obj._collection_name = DEFAULT_COLLECTION_NAME
        obj._k = DEFAULT_NUM_DOCUMENTS
        obj._include_sources = DEFAULT_INCLUDE_SOURCES
        return obj

    def __init__(self, name: str, metadata: WiseAgentMetaData, llm: WiseAgentLLM, vector_db: WiseAgentVectorDB,
                 transport: WiseAgentTransport, collection_name: Optional[str] = DEFAULT_COLLECTION_NAME,
                 k: Optional[int] = DEFAULT_NUM_DOCUMENTS, include_sources: Optional[bool] = DEFAULT_INCLUDE_SOURCES):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            llm (WiseAgentLLM): the LLM to use for processing requests
            vector_db (WiseAgentVectorDB): the vector database to use for retrieving documents
            transport (WiseAgentTransport): the transport to use for communication
            collection_name Optional(str): the name of the collection within the vector database to use for
            retrieving documents, defaults to wise-agent-collection
            k Optional(int): the number of documents to retrieve for each query, defaults to 4
            include_sources Optional(bool): whether to include the sources of the documents that were consulted to
            produce the response, defaults to False
        """
        self._k = k
        self._include_sources = include_sources
        super().__init__(name=name, metadata=metadata, transport=transport, llm=llm,
                         vector_db=vector_db, collection_name=collection_name)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self.collection_name}, transport={self.transport},"
                f"k={self.k}, include_sources={self.include_sources}))")

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage, conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
        """
        Process a request message using retrieval augmented generation (RAG).

        Args:
            request (WiseAgentMessage): the request message to process
            conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.

        Returns:
            Optional[str]: the response to the request message as a string or None if there is
            no string response yet
        """
        retrieved_documents = retrieve_documents_for_rag(request.message, self.vector_db, self.collection_name, self.k)
        llm_response_with_sources = create_and_process_rag_prompt(retrieved_documents, request.message, self.llm,
                                                                  self.include_sources, conversation_history,
                                                                  self.metadata.system_message)
        return llm_response_with_sources

    def process_response(self, response: WiseAgentMessage):
        """Do nothing"""
        return True

    def stop(self):
        """Do nothing"""
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def k(self) -> int:
        """Get the number of documents to retrieve for each query."""
        return self._k

    @property
    def include_sources(self) -> bool:
        """Get whether to include the sources of the documents that were consulted to produce the response."""
        return self._include_sources


class GraphRAGWiseAgent(WiseAgent):
    """
    This agent implementation makes use of Graph Retrieval Augmented Generation (Graph RAG) to answer questions.
    """
    yaml_tag = u'!wiseagents.agents.GraphRAGWiseAgent'
    
    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        obj._k = DEFAULT_NUM_DOCUMENTS
        obj._include_sources = DEFAULT_INCLUDE_SOURCES
        obj._retrieval_query = ""
        obj._params = None
        obj._metadata_filter = None
        return obj

    def __init__(self, name: str, metadata: WiseAgentMetaData, llm: WiseAgentLLM, graph_db: WiseAgentGraphDB,
                 transport: WiseAgentTransport, k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 include_sources: Optional[bool] = DEFAULT_INCLUDE_SOURCES,
                 retrieval_query: Optional[str] = "", params: Optional[Dict[str, Any]] = None,
                 metadata_filter: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            llm (WiseAgentLLM): the LLM to use for processing requests
            graph_db (WiseAgentGraphDB): the graph database to use for retrieving documents
            transport (WiseAgentTransport): the transport to use for communication
            k (Optional[int]): the number of documents to retrieve for each query, defaults to 4
            include_sources Optional(bool): whether to include the sources of the documents that were consulted to
            produce the response, defaults to False
            retrieval_query (Optional[str]): the optional retrieval query to use to obtain sub-graphs connected to nodes
            retrieved from a similarity search
            params (Optional[Dict[str, Any]]): the optional parameters for the query
            metadata_filter (Optional[Dict[str, Any]]): the optional metadata filter to use with similarity search
        """
        self._k = k
        self._include_sources = include_sources
        self._retrieval_query = retrieval_query
        self._params = params
        self._metadata_filter = metadata_filter
        super().__init__(name=name, metadata=metadata, transport=self.transport, llm=llm,
                         graph_db=graph_db)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, llm={self.llm},"
                f"graph_db={self.graph_db}, transport={self.transport}, k={self.k},"
                f"include_sources={self.include_sources}), retrieval_query={self.retrieval_query},"
                f"params={self.params}, metadata_filter={self.metadata_filter})")

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage, conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
        """
        Process a request message by passing it to the RAG agent and sending the response back to the client.

        Args:
            request (WiseAgentMessage): the request message to process
            conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.

        Returns:
            Optional[str]: the response to the request message as a string or None if there is
            no string response yet
        """
        retrieved_documents = retrieve_documents_for_graph_rag(request.message, self.graph_db, self.k,
                                                               self.retrieval_query, self.params, self.metadata_filter)
        llm_response_with_sources = create_and_process_rag_prompt(retrieved_documents, request.message, self.llm, self.include_sources,
                                                                   conversation_history, self.metadata.system_message)
        return llm_response_with_sources

    def process_response(self, response: WiseAgentMessage):
        """Do nothing"""
        return True

    def stop(self):
        """Do nothing"""
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def k(self) -> int:
        """Get the number of documents to retrieve for each query."""
        return self._k

    @property
    def include_sources(self) -> bool:
        """Get whether to include the sources of the documents that were consulted to produce the response."""
        return self._include_sources

    @property
    def retrieval_query(self) -> str:
        """Get the Cypher query to use to obtain sub-graphs connected to nodes retrieved from a similarity search."""
        return self._retrieval_query

    @property
    def params(self) -> Optional[Dict[str, Any]]:
        """Get the optional parameters for the query."""
        return self._params

    @property
    def metadata_filter(self) -> Optional[Dict[str, Any]]:
        """Get the optional metadata filter to use with similarity search."""
        return self._metadata_filter


class BaseCoVeChallengerWiseAgent(WiseAgent):
    """
    This abstract agent implementation is used to challenge the response from a RAG or Graph RAG agent
    using the Chain-of-Verification (CoVe) method (https://arxiv.org/pdf/2309.11495) to try to prevent
    hallucinations.
    """

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        enforce_no_abstract_class_instances(cls, BaseCoVeChallengerWiseAgent)
        obj._k = DEFAULT_NUM_DOCUMENTS
        obj._num_verification_questions = DEFAULT_NUM_VERIFICATION_QUESTIONS
        obj._vector_db = None
        obj._collection_name = DEFAULT_COLLECTION_NAME
        obj._graph_db = None
        return obj

    def __init__(self, name: str, metadata: WiseAgentMetaData, llm: WiseAgentLLM, transport: WiseAgentTransport,
                 k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 num_verification_questions: Optional[int] = DEFAULT_NUM_VERIFICATION_QUESTIONS,
                 vector_db: Optional[WiseAgentVectorDB] = None, collection_name: Optional[str] = DEFAULT_COLLECTION_NAME,
                 graph_db: Optional[WiseAgentGraphDB] = None):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            llm (WiseAgentLLM): the LLM agent to use for processing requests
            transport (WiseAgentTransport): the transport to use for communication
            k Optional(int): the number of documents to retrieve from the vector database, defaults to 4
            num_verification_questions Optional(int): the number of verification questions to generate, defaults to 4
            vector_db (Optional[WiseAgentVectorDB]): the vector DB associated with the agent (to be used for challenging RAG results)
            collection_name (Optional[str]) = "wise-agent-collection": the vector DB collection name associated with the agent
            graph_db (Optional[WiseAgentGraphDB]): the graph DB associated with the agent (to be used for challenging Graph RAG results)
        """
        self._k = k
        self._num_verification_questions = num_verification_questions
        self._vector_db = vector_db
        llm_agent = llm
        super().__init__(name=name, metadata=metadata, transport=transport, llm=llm_agent,
                         vector_db=vector_db, collection_name=collection_name, graph_db=graph_db)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, llm={self.llm},"
                f"k={self.k}, num_verification_questions={self._num_verification_questions},"
                f"transport={self.transport}, vector_db={self.vector_db}, collection_name={self.collection_name},"
                f"graph_db={self.graph_db})")

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage,
                        conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
        """
        Process a message containing a question and a baseline response to the question
        by challenging the baseline response to generate a revised response to the original question.

        Args:
            request (WiseAgentMessage): the request message to process
            conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.

        Returns:
            str: the response to the request message as a string
        """
        return self.create_and_process_chain_of_verification_prompts(request.message, conversation_history)

    def process_response(self, response: WiseAgentMessage):
        """Do nothing"""
        return True

    def stop(self):
        """Do nothing"""
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def k(self) -> int:
        """Get the number of documents to retrieve."""
        return self._k

    @property
    def num_verification_questions(self) -> int:
        """Get the number of verification questions to generate."""
        return self._num_verification_questions

    def create_and_process_chain_of_verification_prompts(self, message: str,
                                                         conversation_history: List[ChatCompletionMessageParam]) -> str:
        """
        Create prompts to challenge the baseline response to a question to try to generate a revised response
        to the original question.

        Args:
            message (str): the message containing the question and baseline response
            conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.
        """

        # plan verifications, taking into account the baseline response and conversation history
        prompt = (f"Given the following question and baseline response, generate a list of {self.num_verification_questions} "
                  f" verification questions that could help determine if there are any mistakes in the baseline response:"
                  f"\n{message}\n"
                  f"Your response should contain only the list of questions, one per line.\n")
        conversation_history.append({"role": "system", "content": self.metadata.system_message or self.llm.system_message})
        conversation_history.append({"role": "user", "content": prompt})
        llm_response = self.llm.process_chat_completion(conversation_history, [])

        # execute verifications, answering questions independently, without the baseline response
        verification_questions = llm_response.choices[0].message.content.splitlines()[:self.num_verification_questions]
        verification_responses = ""
        for question in verification_questions:
            retrieved_documents = self.retrieve_documents(question)
            llm_response = create_and_process_rag_prompt(retrieved_documents, question, self.llm, False,
                                          [], self.metadata.system_message)
            verification_responses = (verification_responses + "Verification Question: " + question + "\n"
                                      + "Verification Result: " + llm_response + "\n")

        # generate the final revised response, conditioned on the baseline response and verification results
        complete_info = message + "\n" + verification_responses
        prompt = (f"Given the following question, baseline response, and a list of verification questions and results,"
                  f" generate a revised response incorporating the verification results:\n{complete_info}\n"
                  f"Your response must contain only the revised response to the question in the JSON format shown below:\n"
                  f"{{'revised': 'Your revised response to the question.'}}\n")

        conversation_history.append({"role": "system", "content": self.metadata.system_message or self.llm.system_message})
        conversation_history.append({"role": "user", "content": prompt})
        llm_response = self.llm.process_chat_completion(conversation_history, [])
        return llm_response.choices[0].message.content

    @abstractmethod
    def retrieve_documents(self, question: str) -> List[Document]:
        """
        Retrieve documents to be used as the context for a RAG or Graph RAG prompt.

        Args:
            question (str): the question to be used to retrieve the documents

        Returns:
            List[Document]: the list of documents retrieved for the question
        """
        ...


class CoVeChallengerRAGWiseAgent(BaseCoVeChallengerWiseAgent):
    """
    This agent implementation is used to challenge the response from a RAG agent using the
    Chain-of-Verification (CoVe) method (https://arxiv.org/pdf/2309.11495) to try to prevent
    hallucinations.
    """
    yaml_tag = u'!wiseagents.agents.CoVeChallengerRAGWiseAgent'

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        obj._collection_name = DEFAULT_COLLECTION_NAME
        obj._k = DEFAULT_NUM_DOCUMENTS
        obj._num_verification_questions = DEFAULT_NUM_VERIFICATION_QUESTIONS
        return obj

    def __init__(self, name: str, metadata: WiseAgentMetaData, llm: WiseAgentLLM, vector_db: WiseAgentVectorDB,
                 transport: WiseAgentTransport, collection_name: Optional[str] = DEFAULT_COLLECTION_NAME,
                 k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 num_verification_questions: Optional[int] = DEFAULT_NUM_VERIFICATION_QUESTIONS):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            llm (WiseAgentLLM): the LLM agent to use for processing requests
            vector_db (WiseAgentVectorDB): the vector database to use for retrieving documents
            transport (WiseAgentTransport): the transport to use for communication
            collection_name (Optional[str]): the name of the collection to use in the vector database, defaults to wise-agents-collection
            k (Optional[int]): the number of documents to retrieve from the vector database, defaults to 4
            num_verification_questions (Optional[int]): the number of verification questions to generate, defaults to 4
        """
        self._k = k
        self._num_verification_questions = num_verification_questions
        super().__init__(name=name, metadata=metadata, transport=transport, llm=llm,
                         vector_db=vector_db, collection_name=collection_name,
                         k=k, num_verification_questions=num_verification_questions)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self.collection_name}, k={self.k},"
                f"num_verification_questions={self._num_verification_questions}, transport={self.transport})")

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage, conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
        """
        Process a message containing a question and a baseline response to the question
        by challenging the baseline response to generate a revised response to the original question.

        Args:
            request (WiseAgentMessage): the request message to process
            conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.

        Returns:
            str: the response to the request message as a string
        """
        llm_response = self.create_and_process_chain_of_verification_prompts(request.message, conversation_history)
        return llm_response

    def process_response(self, response: WiseAgentMessage):
        """Do nothing"""
        return True

    def stop(self):
        """Do nothing"""
        pass

    def retrieve_documents(self, question: str) -> List[Document]:
        return retrieve_documents_for_rag(question, self.vector_db, self.collection_name, self.k)


class CoVeChallengerGraphRAGWiseAgent(BaseCoVeChallengerWiseAgent):
    """
    This agent implementation is used to challenge the response from a Graph RAG agent using the
    Chain-of-Verification (CoVe) method (https://arxiv.org/pdf/2309.11495) to try to prevent
    hallucinations.
    """
    yaml_tag = u'!wiseagents.agents.CoVeChallengerGraphRAGWiseAgent'

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        obj._collection_name = DEFAULT_COLLECTION_NAME
        obj._k = DEFAULT_NUM_DOCUMENTS
        obj._num_verification_questions = DEFAULT_NUM_VERIFICATION_QUESTIONS
        obj._retrieval_query = ""
        obj._params = None
        obj._metadata_filter = None
        return obj

    def __init__(self, name: str, metadata: WiseAgentMetaData, llm: WiseAgentLLM, graph_db: WiseAgentGraphDB,
                 transport: WiseAgentTransport, k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 num_verification_questions: Optional[int] = DEFAULT_NUM_VERIFICATION_QUESTIONS,
                 retrieval_query: Optional[str] = "", params: Optional[Dict[str, Any]] = None,
                 metadata_filter: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            llm (WiseAgentLLM): the LLM agent to use for processing requests
            graph_db (Optional[WiseAgentGraphDB]): the graph database to use for retrieving documents
            transport (WiseAgentTransport): the transport to use for communication
            k (Optional[int]): the number of documents to retrieve from the vector database, defaults to 4
            num_verification_questions (Optional[int]): the number of verification questions to generate, defaults to 4
            retrieval_query (Optional[str]): the optional retrieval query to use to obtain sub-graphs connected to nodes
            retrieved from a similarity search
            params (Optional[Dict[str, Any]]): the optional parameters for the query
            metadata_filter (Optional[Dict[str, Any]]): the optional metadata filter to use with similarity search
        """
        self._k = k
        self._num_verification_questions = num_verification_questions
        self._retrieval_query = retrieval_query
        self._params = params
        self._metadata_filter = metadata_filter
        super().__init__(name=name, metadata=metadata, transport=transport, llm=llm,
                         graph_db=graph_db, k=k,
                         num_verification_questions=num_verification_questions)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, llm={self.llm},"
                f"graph_db={self.graph_db}, k={self.k},num_verification_questions={self._num_verification_questions}"
                f"transport={self.transport}, retrieval_query={self.retrieval_query}, params={self.params}"
                f"metadata_filter={self.metadata_filter})")

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage, conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
        """
        Process a message containing a question and a baseline response to the question
        by challenging the baseline response to generate a revised response to the original question.

        Args:
            request (WiseAgentMessage): the request message to process
            conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.

        Returns:
            str: the response to the request message as a string
        """
        llm_response = self.create_and_process_chain_of_verification_prompts(request.message, conversation_history)
        return llm_response

    def process_response(self, response: WiseAgentMessage):
        """Do nothing"""
        return True

    def stop(self):
        """Do nothing"""
        pass

    @property
    def retrieval_query(self) -> str:
        """Get the Cypher query to use to obtain sub-graphs connected to nodes retrieved from a similarity search."""
        return self._retrieval_query

    @property
    def params(self) -> Optional[Dict[str, Any]]:
        """Get the optional parameters for the query."""
        return self._params

    @property
    def metadata_filter(self) -> Optional[Dict[str, Any]]:
        """Get the optional metadata filter to use with similarity search."""
        return self._metadata_filter

    def retrieve_documents(self, question: str) -> List[Document]:
        return retrieve_documents_for_graph_rag(question, self.graph_db, self.k,
                                                self.retrieval_query, self.params, self.metadata_filter)


def create_and_process_rag_prompt(retrieved_documents: List[Document], question: str, llm: WiseAgentLLM,
                                  include_sources: bool, conversation_history: List[ChatCompletionMessageParam],
                                  system_message: str) -> str:
    """
    Create a RAG prompt and process it with the LLM agent.

    Args:
        retrieved_documents (List[Document]): the list of retrieved documents
        question (str): the question to ask
        llm (WiseAgentLLM): the LLM agent to use for processing the prompt
        conversation_history (List[ChatCompletionMessageParam]): The conversation history that
            can be used while processing the request. If this agent isn't involved in a type of
            collaboration that makes use of the conversation history, this will be an empty list.
        system_message (str): the optional system message to use
    """
    context = "\n".join([document.content for document in retrieved_documents])
    prompt = (f"Answer the question based only on the following context:\n{context}\n"
              f"Question: {question}\n")
    conversation_history.append({"role": "system", "content": system_message or llm.system_message})
    conversation_history.append({"role": "user", "content": prompt})
    llm_response = llm.process_chat_completion(conversation_history, [])

    if include_sources:
        source_documents = ""
        for document in retrieved_documents:
            source_documents += f"Source Document:\n    Content: {document.content}\n    Metadata: {json.dumps(document.metadata)}\n\n"
        return f"{llm_response.choices[0].message.content}\n\nSource Documents:\n{source_documents}"
    else:
        return llm_response.choices[0].message.content


def retrieve_documents_for_rag(question: str, vector_db: WiseAgentVectorDB, collection_name: str, k: int) \
        -> List[Document]:
    """
    Retrieve documents to be used as the context for retrieval augmented generation (RAG).

    Args:
        question (str): the question to be used to retrieve the documents
        vector_db (WiseAgentVectorDB): the vector database to use for retrieving documents
        collection_name (str): the name of the collection within the vector database to use for
            retrieving documents
        k (int): the number of documents to retrieve for a question

    Returns:

    """
    retrieved_documents = vector_db.query([question], collection_name, k)
    if retrieved_documents:
        return retrieved_documents[0]
    else:
        return []


def retrieve_documents_for_graph_rag(question: str, graph_db: WiseAgentGraphDB, k: int,
                                     retrieval_query: Optional[str] = "", params: Optional[Dict[str, Any]] = None,
                                     metadata_filter: Optional[Dict[str, Any]] = None) -> List[Document]:
    """
    Retrieve documents to be used as the context for graph based retrieval augmented generation (Graph RAG).

    Args:
        question (str): the question to be used to retrieve the documents
        graph_db (WiseAgentGraphDB): the graph database to use for retrieving documents
        k (int): the number of documents to retrieve for a question
        retrieval_query (Optional[str]): the optional retrieval query to use to obtain sub-graphs connected to nodes
            retrieved from a similarity search
        params (Optional[Dict[str, Any]]): the optional parameters for the query
        metadata_filter (Optional[Dict[str, Any]]): the optional metadata filter to use with similarity search

    Returns:

    """
    retrieved_documents = graph_db.query_with_embeddings(query=question, k=k,
                                                         retrieval_query=retrieval_query,
                                                         params=params,
                                                         metadata_filter=metadata_filter)
    return retrieved_documents
