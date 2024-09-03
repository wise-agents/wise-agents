import os
import threading

import pytest
from wiseagents import WiseAgentMessage, WiseAgentRegistry
from wiseagents.agents import CoVeChallengerRAGWiseAgent, PassThroughClientAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport
from wiseagents.vectordb import Document, PGVectorLangChainWiseAgentVectorDB



cond = threading.Condition()
assertError : AssertionError = None


@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    original_postgres_user = set_env_variable("POSTGRES_USER", "postgres")
    original_postgres_password = set_env_variable("POSTGRES_PASSWORD", "postgres")
    original_postgres_db = set_env_variable("POSTGRES_DB", "postgres")
    original_stomp_user = set_env_variable("STOMP_USER", "artemis")
    original_stomp_password = set_env_variable("STOMP_PASSWORD", "artemis")

    # Vector DB set up
    pg_vector_db = PGVectorLangChainWiseAgentVectorDB(get_connection_string())
    pg_vector_db.delete_collection("wise-agents-collection")
    pg_vector_db.insert_documents([Document(content="The Olympics took place in Paris in 2024",
                                            metadata={"source": "abc.com"}),
                                   Document(content="The Olympics were held from July 26, 2024 to August 11, 2024",
                                            metadata={"source": "abc.com"}),
                                   Document(content="The US received the most medals at the 2024 Olympics.",
                                            metadata={"source": "abc.com"}),
                                   Document(content="Simone Biles, from the US, won 4 Olympic medals in 2024.",
                                            metadata={"source": "abc.com"})
                                   ],
                                  "wise-agents-collection")
    yield

    # Vector DB clean up
    pg_vector_db.delete_collection("wise-agents-collection")

    # Clean up environment variables
    reset_env_variable("POSTGRES_USER", original_postgres_user)
    reset_env_variable("POSTGRES_PASSWORD", original_postgres_password)
    reset_env_variable("POSTGRES_DB", original_postgres_db)
    reset_env_variable("STOMP_USER", original_stomp_user)
    reset_env_variable("STOMP_PASSWORD", original_stomp_password)
    
    WiseAgentRegistry.clear_agents()
    WiseAgentRegistry.clear_contexts()


def set_env_variable(env_variable: str, value: str) -> str:
    original_value = os.environ.get(env_variable)
    os.environ[env_variable] = value
    return original_value


def reset_env_variable(env_variable: str, original_value: str):
    if original_value is None:
        del os.environ[env_variable]
    else:
        os.environ[env_variable] = original_value


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


@pytest.mark.needsllama
def test_cove_challenger():
    global assertError
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    pg_vector_db = PGVectorLangChainWiseAgentVectorDB(get_connection_string())
    llm1 = OpenaiAPIWiseAgentLLM(system_message="You are a retrieval augmented chatbot. You answer users' questions based on the context provided by the user. If you can't answer the question using the given context, just say you don't know the answer.",
                                 model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                 api_key=groq_api_key)
    agent = CoVeChallengerRAGWiseAgent(name="ChallengerWiseAgent1", description="This is a test agent", llm=llm1, vector_db=pg_vector_db,
                              transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="ChallengerWiseAgent1"),
                                       k=2, num_verification_questions=2)

    with cond:
        client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1", description="This is a test agent",
                                               transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                               )
        client_agent1.set_response_delivery(response_delivered)
        client_agent1.send_request(WiseAgentMessage(f"{{'question': 'How many medals did Biles win at the Winter Olympics in 2024?'\n"
                                                    f"  'response': 'Biles won 4 medals.'\n"
                                                    f"}}",
                                                    "PassThroughClientAgent1"),
                                   "ChallengerWiseAgent1")
        cond.wait()
        if assertError is not None:
            raise assertError
        for agent in WiseAgentRegistry.get_agents():
            print(f"Agent: {agent}")
        for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
            print(f'{message.sender} : {message.message} ')
