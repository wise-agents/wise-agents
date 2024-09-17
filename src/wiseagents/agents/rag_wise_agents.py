import json
import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from wiseagents import WiseAgent, WiseAgentCollaborationType, WiseAgentMessage, WiseAgentTransport
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
        obj._system_message = None
        return obj

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, vector_db: WiseAgentVectorDB,
                 transport: WiseAgentTransport, collection_name: Optional[str] = DEFAULT_COLLECTION_NAME,
                 k: Optional[int] = DEFAULT_NUM_DOCUMENTS, include_sources: Optional[bool] = DEFAULT_INCLUDE_SOURCES,
                 system_message: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            description (str): a description of the agent
            llm (WiseAgentLLM): the LLM to use for processing requests
            vector_db (WiseAgentVectorDB): the vector database to use for retrieving documents
            transport (WiseAgentTransport): the transport to use for communication
            collection_name Optional(str): the name of the collection within the vector database to use for
            retrieving documents, defaults to wise-agent-collection
            k Optional(int): the number of documents to retrieve for each query, defaults to 4
            include_sources Optional(bool): whether to include the sources of the documents that were consulted to
            produce the response, defaults to False
        """
        self._name = name
        self._description = description
        self._transport = transport
        self._vector_db = vector_db
        self._collection_name = collection_name
        self._k = k
        self._include_sources = include_sources
        super().__init__(name=name, description=description, transport=self.transport, llm=llm,
                         vector_db=vector_db, collection_name=collection_name, system_message=system_message)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self.collection_name}, transport={self.transport},"
                f"k={self.k}, include_sources={self.include_sources}), system_message={self.system_message})")

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
        retrieved_documents = self.vector_db.query([request.message], self.collection_name, self.k)
        llm_response_with_sources = create_and_process_rag_prompt(retrieved_documents[0], request.message, self.llm,
                                                                   self.include_sources, conversation_history,
                                                                   self.system_message)
        return llm_response_with_sources

    def process_response(self, response: WiseAgentMessage):
        """Do nothing"""
        return True

    def get_recipient_agent_name(self, message):
        """Return the name of the agent to send the message to."""
        return self.name

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
        obj._system_message = None
        return obj

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, graph_db: WiseAgentGraphDB,
                 transport: WiseAgentTransport, k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 include_sources: Optional[bool] = DEFAULT_INCLUDE_SOURCES,
                 retrieval_query: Optional[str] = "", params: Optional[Dict[str, Any]] = None,
                 metadata_filter: Optional[Dict[str, Any]] = None, system_message: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            description (str): a description of the agent
            llm (WiseAgentLLM): the LLM to use for processing requests
            graph_db (WiseAgentGraphDB): the graph database to use for retrieving documents
            transport (WiseAgentTransport): the transport to use for communication
            k Optional(int): the number of documents to retrieve for each query, defaults to 4
            include_sources Optional(bool): whether to include the sources of the documents that were consulted to
            produce the response, defaults to False
            retrieval_query Optional(str): the optional retrieval query to use to obtain sub-graphs connected to nodes
            retrieved from a similarity search
            params (Optional[Dict[str, Any]]): the optional parameters for the query
            metadata_filter (Optional[Dict[str, Any]]): the optional metadata filter to use with similarity search
            system_message (Optional[str]): the optional system message to be used by the collaborator when processing
            chat completions using its LLM
        """
        self._name = name
        self._description = description
        self._transport = transport
        self._graph_db = graph_db
        self._k = k
        self._include_sources = include_sources
        self._retrieval_query = retrieval_query
        self._params = params
        self._metadata_filter = metadata_filter
        super().__init__(name=name, description=description, transport=self.transport, llm=llm,
                         graph_db=graph_db, system_message=system_message)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"graph_db={self.graph_db}, transport={self.transport}, k={self.k},"
                f"include_sources={self.include_sources}), retrieval_query={self.retrieval_query},"
                f"params={self.params}, metadata_filter={self.metadata_filter}, system_message={self.system_message})")

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
        retrieved_documents = self.graph_db.query_with_embeddings(query=request.message, k=self.k,
                                                                  retrieval_query=self.retrieval_query,
                                                                  params=self.params,
                                                                  metadata_filter=self.metadata_filter)
        llm_response_with_sources = create_and_process_rag_prompt(retrieved_documents, request.message, self.llm, self.include_sources,
                                                                   conversation_history, self.system_message)
        return llm_response_with_sources

    def process_response(self, response: WiseAgentMessage):
        """Do nothing"""
        return True

    def get_recipient_agent_name(self, message):
        """Return the name of the agent to send the message to."""
        return self.name

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
    yaml_tag = u'!wiseagents.agents.BaseCoVeChallengerWiseAgent'

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        obj._k = DEFAULT_NUM_DOCUMENTS
        obj._num_verification_questions = 4
        obj._num_verification_questions = DEFAULT_NUM_VERIFICATION_QUESTIONS
        obj._vector_db = None
        obj._collection_name = DEFAULT_COLLECTION_NAME
        obj._graph_db = None
        obj._system_message = None
        return obj

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, transport: WiseAgentTransport,
                 k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 num_verification_questions: Optional[int] = DEFAULT_NUM_VERIFICATION_QUESTIONS,
                 vector_db: Optional[WiseAgentVectorDB] = None, collection_name: Optional[str] = DEFAULT_COLLECTION_NAME,
                 graph_db: Optional[WiseAgentGraphDB] = None, system_message: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            description (str): a description of the agent
            llm (WiseAgentLLM): the LLM agent to use for processing requests
            transport (WiseAgentTransport): the transport to use for communication
            k Optional(int): the number of documents to retrieve from the vector database, defaults to 4
            num_verification_questions Optional(int): the number of verification questions to generate, defaults to 4
            vector_db (Optional[WiseAgentVectorDB]): the vector DB associated with the agent (to be used for challenging RAG results)
            collection_name (Optional[str]) = "wise-agent-collection": the vector DB collection name associated with the agent
            graph_db (Optional[WiseAgentGraphDB]): the graph DB associated with the agent (to be used for challenging Graph RAG results)
            system_message (Optional[str]): the optional system message to be used by the collaborator when processing
            chat completions using its LLM
        """
        self._name = name
        self._description = description
        self._transport = transport
        self._k = k
        self._num_verification_questions = num_verification_questions
        self._vector_db = vector_db
        self._collection_name = collection_name
        self._graph_db = graph_db
        llm_agent = llm
        super().__init__(name=name, description=description, transport=self.transport, llm=llm_agent,
                         vector_db=vector_db, collection_name=collection_name, graph_db=graph_db,
                         system_message=system_message)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"k={self.k}, num_verification_questions={self._num_verification_questions},"
                f"transport={self.transport}, vector_db={self.vector_db}, collection_name={self.collection_name},"
                f"graph_db={self.graph_db}, system_message={self.system_message})")

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

    def get_recipient_agent_name(self, message):
        """Return the name of the agent to send the message to."""
        return self.name

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
        conversation_history.append({"role": "system", "content": self.system_message or self.llm.system_message})
        conversation_history.append({"role": "user", "content": prompt})
        llm_response = self.llm.process_chat_completion(conversation_history, [])

        # execute verifications, answering questions independently, without the baseline response
        verification_questions = llm_response.choices[0].message.content.splitlines()
        verification_responses = ""
        for question in verification_questions:
            retrieved_documents = self.retrieve_documents(question)
            create_and_process_rag_prompt(retrieved_documents, question, self.llm, False,
                                          [], self.system_message)
            verification_responses = (verification_responses + "Verification Question: " + question + "\n"
                                      + "Verification Result: " + llm_response.choices[0].message.content + "\n")

        # generate the final revised response, conditioned on the baseline response and verification results
        complete_info = message + "\n" + verification_responses
        prompt = (f"Given the following question, baseline response, and a list of verification questions and results,"
                  f" generate a revised response incorporating the verification results:\n{complete_info}\n"
                  f"Your response must contain only the revised response to the question in the JSON format shown below:\n"
                  f"{{'revised': 'Your revised response to the question.'}}\n")

        conversation_history.append({"role": "system", "content": self.system_message or self.llm.system_message})
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
        obj._system_message = None
        return obj

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, vector_db: WiseAgentVectorDB,
                 transport: WiseAgentTransport, collection_name: Optional[str] = DEFAULT_COLLECTION_NAME,
                 k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 num_verification_questions: Optional[int] = DEFAULT_NUM_VERIFICATION_QUESTIONS,
                 system_message: Optional[str] = None):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            description (str): a description of the agent
            llm (WiseAgentLLM): the LLM agent to use for processing requests
            vector_db (WiseAgentVectorDB): the vector database to use for retrieving documents
            transport (WiseAgentTransport): the transport to use for communication
            collection_name (Optional[str]): the name of the collection to use in the vector database, defaults to wise-agents-collection
            k (Optional[int]): the number of documents to retrieve from the vector database, defaults to 4
            num_verification_questions (Optional[int]): the number of verification questions to generate, defaults to 4
            system_message (Optional[str]): the optional system message to be used by the collaborator when processing
            chat completions using its LLM
        """
        self._name = name
        self._description = description
        self._transport = transport
        self._vector_db = vector_db
        self._collection_name = collection_name
        self._k = k
        self._num_verification_questions = num_verification_questions
        llm_agent = llm
        super().__init__(name=name, description=description, transport=self.transport, llm=llm_agent,
                         system_message=system_message, vector_db=vector_db, collection_name=collection_name,
                         k=k, num_verification_questions=num_verification_questions)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self.collection_name}, k={self.k},"
                f"num_verification_questions={self._num_verification_questions}, transport={self.transport},"
                f"system_message={self.system_message})")

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

    def get_recipient_agent_name(self, message):
        """Return the name of the agent to send the message to."""
        return self.name

    def stop(self):
        """Do nothing"""
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def k(self) -> int:
        """Get the number of documents to retrieve from the vector database."""
        return self._k

    @property
    def num_verification_questions(self) -> int:
        """Get the number of verification questions to generate."""
        return self._num_verification_questions

    def retrieve_documents(self, question: str) -> List[Document]:
        retrieved_documents = self.vector_db.query([question], self.collection_name, self.k)
        if retrieved_documents:
            return retrieved_documents[0]
        else:
            return []


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
        return f"{llm_response.content}\n\nSource Documents:\n{source_documents}"
    else:
        return llm_response.choices[0].message.content
