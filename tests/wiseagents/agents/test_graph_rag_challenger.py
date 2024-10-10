import logging
import os
import threading
import uuid

import pytest
from wiseagents import WiseAgentMessage, WiseAgentMetaData, WiseAgentRegistry
from wiseagents.agents import PassThroughClientAgent
from wiseagents.agents.rag_wise_agents import CoVeChallengerGraphRAGWiseAgent

from wiseagents.graphdb import Entity, GraphDocument, Neo4jLangChainWiseAgentGraphDB, Relationship, Source
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport
from tests.wiseagents import assert_standard_variables_set, mock_open_ai_for_ci, mock_open_ai_chat_completion, get_user_messages

cond = threading.Condition()
assertError : AssertionError = None


def _mock_llm(*args, **kwargs):
    messages = get_user_messages(kwargs["messages"])
    if len (messages) == 1:
        # This is either the planning query, or the generated ones
        if "How many medals did Biles win at the Winter Olympics in 2024?" in messages[0]:
            return mock_open_ai_chat_completion(
                "Is Simone Biles a typically Winter Olympics athlete or does she specialize in the Summer Olympics?\n"
                "Did the 2024 Winter Olympics occur prior to the generation of this knowledge?")
        elif "Is Simone Biles a typically Winter Olympics athlete" in messages[0]:
            return mock_open_ai_chat_completion("Based on the provided context, I don't know the answer.")
        elif "Did the 2024 Winter Olympics occur prior to the generation of this knowledge?" in messages[0]:
            return mock_open_ai_chat_completion("I don't know the answer.")
    elif len(messages) == 2:
        if "How many medals did Biles win at the Winter Olympics in 2024?" in messages[0] and \
                "Is Simone Biles a typically Winter Olympics athlete" in messages[1] and \
                "Did the 2024 Winter Olympics occur prior to the generation of this knowledge?" in messages[1]:
            return mock_open_ai_chat_completion("I don't know how many medals Biles won at the Winter Olympics in 2024.")

    try:
        assert False, f"Unexpected messages received by the Mock LLM {messages}"
    except AssertionError as e:
        global assertError
        assertError = e
        with cond:
            cond.notify()


collection_name = "test-vector-db"
@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():

    assert_standard_variables_set()

    # Ensure that nothing exists the graph DB
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)
    graph_db.query("MATCH (n)-[r]-() DELETE r")
    graph_db.query("MATCH (n) DELETE n")

    page_content = "Simone Biles, from the US, participated in the 2024 Olympics and won 4 medals."
    person = Entity(id=str(uuid.uuid4()), metadata={"name": "Simone Biles", "type": "person"})
    medals = Entity(id=str(uuid.uuid4()), metadata={"name": "4 medals", "type": "medals"})
    event = Entity(id=str(uuid.uuid4()), metadata={"name": "2024 Olympics", "type": "event"})
    country = Entity(id=str(uuid.uuid4()), metadata={"name": "US", "type": "country"})
    graph_document = GraphDocument(entities=[person, medals, event, country],
                                   relationships=[Relationship(source=person, target=medals, label="won"),
                                                  Relationship(source=person, target=event,
                                                               label="participated in"),
                                                  Relationship(source=person, target=country,
                                                               label="is from")],
                                   source=Source(content=page_content))
    graph_db.insert_graph_documents([graph_document])
    graph_db.refresh_schema()

    yield

    # Delete all relationships and entities from graph_db
    graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                              url="bolt://localhost:7687", refresh_graph_schema=False)
    graph_db.query("MATCH (n)-[r]-() DELETE r")
    graph_db.query("MATCH (n) DELETE n")
    graph_db.delete_vector_db()
    graph_db.close()


def get_connection_string():
    return f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@localhost:6024/{os.environ['POSTGRES_DB']}"


def response_delivered(message: WiseAgentMessage):
    global assertError
    with cond:
        response = message.message
        try:
            assert "4 medals" not in response
        except AssertionError:
            assertError = AssertionError
        print(f"C Response delivered: {response}")
        cond.notify()


def test_cove_challenger_graph_rag(mocker):
    mock_open_ai_for_ci(mocker, _mock_llm)
    try:
        global assertError
        groq_api_key = os.getenv("GROQ_API_KEY")

        graph_db = Neo4jLangChainWiseAgentGraphDB(properties=["name", "type"], collection_name=collection_name,
                                                  url="bolt://localhost:7687", refresh_graph_schema=False)
        llm1 = OpenaiAPIWiseAgentLLM(system_message="You are a retrieval augmented chatbot. You answer users' questions based on the context provided by the user. If you can't answer the question using the given context, just say you don't know the answer.",
                                    model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                    api_key=groq_api_key)
        agent = CoVeChallengerGraphRAGWiseAgent(name="GraphRAGChallengerWiseAgent1", metadata=WiseAgentMetaData(description="This is a test agent"), llm=llm1, graph_db=graph_db,
                                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="GraphRAGChallengerWiseAgent1"),
                                                k=2, num_verification_questions=2)
        WiseAgentRegistry.create_context("default")

        with cond:
            client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1", metadata=WiseAgentMetaData(description="This is a test agent"),
                                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                )
            client_agent1.set_response_delivery(response_delivered)
            client_agent1.send_request(WiseAgentMessage(message = f"{{'question': 'How many medals did Biles win at the Winter Olympics in 2024?'\n"
                                                        f"  'response': 'Biles won 4 medals.'\n"
                                                        f"}}", context_name="default", sender="PassThroughClientAgent1"),
                                    "GraphRAGChallengerWiseAgent1")
            cond.wait(timeout=300)
            if assertError is not None:
                raise assertError
            logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")
            for message in WiseAgentRegistry.get_context('default').message_trace:
                logging.debug(f'{message}')
    finally:        
        #stopping the agents
        client_agent1.stop_agent()
        agent.stop_agent()
        WiseAgentRegistry.remove_context("default")
