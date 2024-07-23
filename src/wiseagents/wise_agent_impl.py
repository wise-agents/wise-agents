import json
import logging
from typing import Callable, List, Optional

from wiseagents.graphdb import WiseAgentGraphDB

from wiseagents.vectordb import Document, WiseAgentVectorDB

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentTransport
from wiseagents.llm.wise_agent_LLM import WiseAgentLLM
from wiseagents.transports.stomp import StompWiseAgentTransport


class PassThroughClientAgent(WiseAgent):
    '''This agent is used mainly for test purposes. It just passes the request to another agent and sends back the response to the client.'''
    '''Use Stomp protocol'''
    yaml_tag = u'!wiseagents.PassThroughClientAgent'
    def __init__(self, name, description , transport):
        self._name = name
        super().__init__(name=name, description=description, transport=transport, llm=None)
    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(name={self.name}, description={self.description})"
    def process_request(self, request):
        #print(f"CA Request received: {request}")
        #just pass to the ohther agent
        self.send_request(WiseAgentMessage(request, self.name), 'WiseIntelligentAgent' )
        return True
    def process_response(self, response):
        #print(f"CA Response received: {response}")
        #send back response to the client
        self.response_delivery(response)
        return True
    def process_event(self, event):
        return True
    def process_error(self, error):
        return True
    def get_recipient_agent_name(self, message):
        return self.name
    def stop(self):
        pass
    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name
    @property
    def response_delivery(self) -> Optional[Callable[[], WiseAgentMessage]]:
        return self._response_delivery
    def set_response_delivery(self, response_delivery: Callable[[], WiseAgentMessage]):
        self._response_delivery = response_delivery
class LLMOnlyWiseAgent(WiseAgent):
    '''This agent implementation is used to test the LLM only agent.'''
    '''Use Stomp protocol''' 
    yaml_tag = u'!wiseagents.LLMOnlyWiseAgent'
    def __init__(self, name: str, description: str, llm : WiseAgentLLM, trasport: WiseAgentTransport):
        self._name = name
        self._description = description
        self._transport = trasport
        llm_agent = llm
        super().__init__(name=name, description=description, transport=self.transport, llm=llm_agent)

    def __repr__(self):
        '''Return a string representation of the agent.'''
        return f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm}, transport={self.transport})"
        
    def process_event(self, event):
        return True
    def process_error(self, error):
        logging.error(error)
        return True
    def process_request(self, request: WiseAgentMessage):
        #print(f"IA Request received: {request}")
        llm_response = self.llm.process(request.message)
        self.send_response(WiseAgentMessage(llm_response.content, self.name), request.sender )
        return True
    def process_response(self, response : WiseAgentMessage):
        #print(f"Response received: {response}")
        return True
    def get_recipient_agent_name(self, message):
        return self.name
    def stop(self):
        pass    
    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name


class RAGWiseAgent(WiseAgent):
    """
    This agent implementation is used to test the RAG agent.
    Use Stomp protocol
    """
    yaml_tag = u'!wiseagents.RAGWiseAgent'

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, vector_db: WiseAgentVectorDB,
                 transport: WiseAgentTransport, collection_name: Optional[str] = "wise-agents-collection"):
        self._name = name
        self._description = description
        self._transport = transport
        self._vector_db = vector_db
        self._collection_name = collection_name
        llm_agent = llm
        super().__init__(name=name, description=description, transport=self.transport, llm=llm_agent,
                         vector_db=vector_db, collection_name=collection_name)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"vector_db={self.vector_db}, collection_name={self.collection_name}, transport={self.transport})")

    def process_event(self, event):
        return True

    def process_error(self, error):
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage):
        retrieved_documents = self.vector_db.query([request.message], self.collection_name, 4)
        llm_response_with_sources = _create_and_process_rag_prompt(retrieved_documents[0], request.message, self.llm)
        self.send_response(WiseAgentMessage(llm_response_with_sources, self.name), request.sender)
        return True

    def process_response(self, response: WiseAgentMessage):
        return True

    def get_recipient_agent_name(self, message):
        return self.name

    def stop(self):
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

class GraphRAGWiseAgent(WiseAgent):
    """
    This agent implementation is used to test a knowledge graph based RAG agent.
    Use Stomp protocol
    """
    yaml_tag = u'!wiseagents.GraphRAGWiseAgent'

    def __init__(self, name: str, description: str, llm: WiseAgentLLM, graph_db: WiseAgentGraphDB,
                 transport: WiseAgentTransport):
        self._name = name
        self._description = description
        self._transport = transport
        self._graph_db = graph_db
        llm_agent = llm
        super().__init__(name=name, description=description, transport=self.transport, llm=llm_agent,
                         graph_db=graph_db)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, description={self.description}, llm={self.llm},"
                f"graph_db={self.graph_db}, transport={self.transport})")

    def process_event(self, event):
        return True

    def process_error(self, error):
        logging.error(error)
        return True

    def process_request(self, request: WiseAgentMessage):
        self.graph_db.create_vector_db_from_graph_db(properties=["name", "type"], collection_name="test_vector_db")
        retrieved_documents = self.graph_db.query_with_embeddings(request.message, 4)
        llm_response_with_sources = _create_and_process_rag_prompt(retrieved_documents, request.message, self.llm)
        self.send_response(WiseAgentMessage(llm_response_with_sources, self.name), request.sender)
        return True

    def process_response(self, response: WiseAgentMessage):
        return True

    def get_recipient_agent_name(self, message):
        return self.name

    def stop(self):
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name


def _create_and_process_rag_prompt(retrieved_documents: List[Document], question: str, llm: WiseAgentLLM) -> str:
    context = "\n".join([document.content for document in retrieved_documents])
    prompt = (f"Answer the question based only on the following context:\n{context}\n"
              f"Question: {question}\n")
    llm_response = llm.process(prompt)

    source_documents = ""
    for document in retrieved_documents:
        source_documents += f"Source Document:\n    Content: {document.content}\n    Metadata: {json.dumps(document.metadata)}\n\n"
    llm_response_with_sources = f"{llm_response.content}\n\nSource Documents:\n{source_documents}"
    return llm_response_with_sources
