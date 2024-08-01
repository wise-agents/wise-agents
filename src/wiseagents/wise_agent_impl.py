import json
import logging
from typing import Callable, List, Optional

from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel

from wiseagents.graphdb import WiseAgentGraphDB

from wiseagents.vectordb import Document, WiseAgentVectorDB

from wiseagents import WiseAgent, WiseAgentMessage, WiseAgentRegistry, WiseAgentTransport, WiseAgentTool
from wiseagents.llm.wise_agent_LLM import WiseAgentLLM


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
        llm_response = self.llm.process_single_prompt(request.message)
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


    
    

class LLMWiseAgentWithTools(WiseAgent):
    '''This agent implementation is used to test the LLM agent providing a simple tool.'''
    '''Use Stomp protocol''' 
    yaml_tag = u'!wiseagents.LLMWiseAgentWithTools'
    def __init__(self, name: str, description: str, llm : WiseAgentLLM, transport: WiseAgentTransport, tools: List[str]):
        self._name = name
        self._description = description
        self._transport = transport
        llm_agent = llm
        self._tools = tools
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
        logging.debug(f"IA Request received: {request}")
        messages = []
        messages.append({"role": "system", "content": self.llm.system_message})
        messages.append({"role": "user", "content": request.message})
        
        tools = []
        for tool in self._tools:
            tools.append(WiseAgentRegistry.get_tool(tool).get_tool_OpenAI_format())
            
       #{"name":"Tool1","description":"This is a test tool","parameters":{"param1":{"description":"This is a test parameter","type":"str","default":"value1","required":true}}}
        logging.debug(f"messages: {messages}, Tools: {tools}")    
        llm_response = self.llm.process_chat_complition(messages, tools)
        
        ##calling tool
        response_message = llm_response.choices[0].message
        tool_calls = response_message.tool_calls
        logging.debug(f"Tool calls: {tool_calls}")
        logging.debug(f"Response message: {response_message}")
        # Step 2: check if the model wanted to call a function
        if tool_calls is not None:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            messages.append(response_message)  # extend conversation with assistant's reply
            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                wise_agent_tool : WiseAgentTool = WiseAgentRegistry.get_tool(function_name)
                function_args = json.loads(tool_call.function.arguments)
                function_response = wise_agent_tool.exec(**function_args)
                #function_response = function_to_call(
                 #    location=function_args.get("location"),
                 #   unit=function_args.get("unit"),
                #)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response
            llm_response = self.llm.process_chat_complition(messages, tools)
            response_message = llm_response.choices[0].message
        

        logging.debug(f"sending response {response_message.content} to: {request.sender}")
        self.send_response(WiseAgentMessage(response_message.content, self.name), request.sender )
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
        retrieved_documents = self.graph_db.query_with_embeddings(query=request.message, k=1, retrieval_query=self._get_retrieval_query())
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

    def _get_retrieval_query(self) -> str:
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


def _create_and_process_rag_prompt(retrieved_documents: List[Document], question: str, llm: WiseAgentLLM) -> str:
    context = "\n".join([document.content for document in retrieved_documents])
    prompt = (f"Answer the question based only on the following context:\n{context}\n"
              f"Question: {question}\n")
    llm_response = llm.process_single_prompt(prompt)

    source_documents = ""
    for document in retrieved_documents:
        source_documents += f"Source Document:\n    Content: {document.content}\n    Metadata: {json.dumps(document.metadata)}\n\n"
    llm_response_with_sources = f"{llm_response.content}\n\nSource Documents:\n{source_documents}"
    return llm_response_with_sources
