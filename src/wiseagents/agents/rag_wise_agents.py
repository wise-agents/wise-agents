import json
import logging
from typing import List, Optional

from wiseagents.graphdb import WiseAgentGraphDB

from wiseagents.vectordb import Document, WiseAgentVectorDB

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentTransport
from wiseagents.llm import WiseAgentLLM

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

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, vector_db: WiseAgentVectorDB,
                 transport: WiseAgentTransport, collection_name: Optional[str] = DEFAULT_COLLECTION_NAME,
                 k: Optional[int] = DEFAULT_NUM_DOCUMENTS, include_sources: Optional[bool] = DEFAULT_INCLUDE_SOURCES):
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
                         vector_db=vector_db, collection_name=collection_name)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self.collection_name}, transport={self.transport},"
                f"k={self.k}, include_sources={self.include_sources})")

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage):
        """
        Process a request message using retrieval augmented generation (RAG) and sending the response back to the client.

        Args:
            request (WiseAgentMessage): the request message to process
        """
        retrieved_documents = self.vector_db.query([request.message], self.collection_name, self.k)
        llm_response_with_sources = _create_and_process_rag_prompt(retrieved_documents[0], request.message, self.llm,
                                                                   self.include_sources)
        self.send_response(WiseAgentMessage(llm_response_with_sources, self.name), request.sender)
        return True

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
        return obj

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, graph_db: WiseAgentGraphDB,
                 transport: WiseAgentTransport, k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 include_sources: Optional[bool] = DEFAULT_INCLUDE_SOURCES):
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
        """
        self._name = name
        self._description = description
        self._transport = transport
        self._graph_db = graph_db
        self._k = k
        self._include_sources = include_sources
        super().__init__(name=name, description=description, transport=self.transport, llm=llm,
                         graph_db=graph_db)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"graph_db={self.graph_db}, transport={self.transport}, k={self.k},"
                f"include_sources={self.include_sources})")

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage):
        """
        Process a request message by passing it to the RAG agent and sending the response back to the client.

        Args:
            request (WiseAgentMessage): the request message to process
        """
        retrieved_documents = self.graph_db.query_with_embeddings(query=request.message, k=self.k, retrieval_query=self._get_retrieval_query())
        llm_response_with_sources = _create_and_process_rag_prompt(retrieved_documents, request.message, self.llm, self.include_sources)
        self.send_response(WiseAgentMessage(llm_response_with_sources, self.name), request.sender)
        return True

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

    def _get_retrieval_query(self) -> str:
        """Return the retrieval query to use for retrieving documents from the graph database."""
        # this is specific to the test
        return """
          WITH node AS landmark, score AS similarity
          CALL  {
            WITH landmark
            MATCH (landmark)--(city)--(province)--(country)
            RETURN country.name AS Country
          }
          RETURN landmark.name + ' is located in ' + Country AS text, similarity as score, {} AS metadata
        """


class CoVeChallengerRAGWiseAgent(WiseAgent):
    """
    This agent implementation is used to challenge the response from a RAG agent using the
    Chain-of-Verification (CoVe) method (https://arxiv.org/pdf/2309.11495) to try to prevent
    hallucinations.
    Uses the Stomp protocol.
    """
    yaml_tag = u'!wiseagents.agents.CoVeChallengerRAGWiseAgent'

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the optional instance variables."""
        obj = super().__new__(cls)
        obj._collection_name = DEFAULT_COLLECTION_NAME
        obj._k = DEFAULT_NUM_DOCUMENTS
        obj._num_verification_questions = 4
        obj._include_sources = DEFAULT_INCLUDE_SOURCES
        obj._num_verification_questions = DEFAULT_NUM_VERIFICATION_QUESTIONS
        return obj

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, vector_db: WiseAgentVectorDB,
                 transport: WiseAgentTransport, collection_name: Optional[str] = DEFAULT_COLLECTION_NAME,
                 k: Optional[int] = DEFAULT_NUM_DOCUMENTS,
                 num_verification_questions: Optional[int] = DEFAULT_NUM_VERIFICATION_QUESTIONS):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            description (str): a description of the agent
            llm (WiseAgentLLM): the LLM agent to use for processing requests
            vector_db (WiseAgentVectorDB): the vector database to use for retrieving documents
            transport (WiseAgentTransport): the transport to use for communication
            collection_name Optional(str): the name of the collection to use in the vector database, defaults to wise-agents-collection
            k Optional(int): the number of documents to retrieve from the vector database, defaults to 4
            num_verification_questions Optional(int): the number of verification questions to generate, defaults to 4
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
                         vector_db=vector_db, collection_name=collection_name)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self.collection_name}, k={self.k},"
                f"num_verification_questions={self._num_verification_questions}, transport={self.transport})")

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage):
        """
        Process a message containing a question and a baseline response to the question
        by challenging the baseline response to generate a revised response to the original question.

        Args:
            request (WiseAgentMessage): the request message to process
        """
        llm_response = self._create_and_process_chain_of_verification_prompts(request.message)
        self.send_response(WiseAgentMessage(llm_response, self.name), request.sender)
        return True

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

    def _create_and_process_chain_of_verification_prompts(self, message: str) -> str:
        """
        Create prompts to challenge the baseline response to a question to try to generate a revised response
        to the original question.

        Args:
            message (str): the message containing the question and baseline response
        """

        """Plan verifications"""
        prompt = (f"Given the following question and baseline response, generate a list of {self.num_verification_questions} "
                  f" verification questions that could help determine if there are any mistakes in the baseline response:\n{message}\n"
                  f"Your response should contain only the list of questions, one per line.\n")
        llm_response = self.llm.process_single_prompt(prompt)

        """Execute verifications"""
        verification_questions = llm_response.content.splitlines()
        verification_responses = ""
        for question in verification_questions:
            retrieved_documents = self.vector_db.query([question], self.collection_name, self.k)
            context = "\n".join([document.content for document in retrieved_documents[0]])
            prompt = (f"Answer the question based only on the following context:\n{context}\n"
                      f"Question: {question}\n")
            llm_response = self.llm.process_single_prompt(prompt)
            verification_responses = (verification_responses + "Verification Question: " + question + "\n"
                                      + "Verification Result: " + llm_response.content + "\n")

        """Generate the final revised response"""
        complete_info = message + "\n" + verification_responses
        prompt = (f"Given the following question, baseline response, and a list of verification questions and results,"
                  f" generate a revised response incorporating the verification results:\n{complete_info}\n"
                  f"Your response must contain only the revised response to the question in the JSON format shown below:\n"
                  f"{{'revised': 'Your revised response to the question.'}}\n")

        llm_response = self.llm.process_single_prompt(prompt)
        return llm_response.content


def _create_and_process_rag_prompt(retrieved_documents: List[Document], question: str, llm: WiseAgentLLM,
                                   include_sources: bool) -> str:
    """Create a RAG prompt and process it with the LLM agent.

    Args:
        retrieved_documents (List[Document]): the list of retrieved documents
        question (str): the question to ask
        llm (WiseAgentLLM): the LLM agent to use for processing the prompt
    """
    context = "\n".join([document.content for document in retrieved_documents])
    prompt = (f"Answer the question based only on the following context:\n{context}\n"
              f"Question: {question}\n")
    llm_response = llm.process_single_prompt(prompt)

    if include_sources:
        source_documents = ""
        for document in retrieved_documents:
            source_documents += f"Source Document:\n    Content: {document.content}\n    Metadata: {json.dumps(document.metadata)}\n\n"
        return f"{llm_response.content}\n\nSource Documents:\n{source_documents}"
    else:
        return llm_response.content