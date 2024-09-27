import logging
import os
import threading

import pytest

from wiseagents import WiseAgentMessage, WiseAgentMetaData, WiseAgentRegistry
from wiseagents.agents import LLMOnlyWiseAgent, PassThroughClientAgent, \
    PhasedCoordinatorWiseAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport

cond = threading.Condition()
assertError : AssertionError = None

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    
    

def final_response_delivered(message: WiseAgentMessage):
    with cond:
        response = message.message
        try:
            assert response
            print(f"C Response delivered: {response}")
        except AssertionError:
            logging.info(f"assertion failed")
            assertError = AssertionError
        cond.notify()


def test_phased_coordinator():
    """
    Requires STOMP_USER, STOMP_PASSWORD, and a Groq API_KEY.
    """
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")
        global assertError

        llm = OpenaiAPIWiseAgentLLM(system_message="You are a helpful assistant.",
                                    model_name="llama-3.1-70b-versatile",
                                    remote_address="https://api.groq.com/openai/v1",
                                    api_key=groq_api_key)

        agent1 = PhasedCoordinatorWiseAgent(name="Coordinator", 
                                            metadata=WiseAgentMetaData(description="This is a coordinator agent",
                                                                       system_message="You will be coordinating a group of agents to solve a problem."),
                                            llm=llm,
                                            transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Coordinator"),
                                            phases=["Information Gathering", "Verification of Information", "Analysis"],
                                            max_iterations=2)

        agent2 = LLMOnlyWiseAgent(name="Agent2", metadata=WiseAgentMetaData(description="This agent provides information about error messages using Source1",
                                                                            system_message="You are a helpful assistant that will provide information about the given error message"),
                                  llm=llm,
                                  transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                    agent_name="Agent2"))

        agent3 = LLMOnlyWiseAgent(name="Agent3", metadata=WiseAgentMetaData(description="This agent provides information about error messages using Source2",
                                                                            system_message="You are a helpful assistant that will provide information about the given error message"),
                                  llm=llm,
                                  transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                    agent_name="Agent3"))

        agent4 = LLMOnlyWiseAgent(name="Agent4",
                                  metadata=WiseAgentMetaData(description="This agent describes the underlying cause of a problem given information about the problem. This agent" +
                                              " should be called after getting information about the problem using Agent2 or Agent3.",
                                              system_message="You are a helpful assistant that will determine the underlying cause of a problem given information about the problem"),
                                  llm=llm,
                                  transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                    agent_name="Agent4"))

        agent5 = LLMOnlyWiseAgent(name="Agent5",
                                  metadata=WiseAgentMetaData(description="This agent is used to verify if the information provided by other agents is accurate. This " +
                                              "agent should be called after getting information about a problem using Agent2 or Agent3. This agent " +
                                              "should be called before calling Agent4.",
                                              system_message="You will determine if the information provided by other agents is accurate."),
                                  llm=llm,
                                  transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                    agent_name="Agent5"))

        with cond:
            client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1", metadata=WiseAgentMetaData(description="This is a test agent"),
                                                   transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                   )
            client_agent1.set_response_delivery(final_response_delivered)
            client_agent1.send_request(WiseAgentMessage("How do I prevent the following exception from occurring:"
                                                        "Exception Details: java.lang.NullPointerException at com.example.ExampleApp.processData(ExampleApp.java:47)",
                                                        "PassThroughClientAgent1"),
                                       "Coordinator")
            cond.wait()
            if assertError is not None:
                logging.info(f"assertion failed")
                raise assertError

            logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")
            for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
                logging.debug(f'{message}')
    finally:
        #stop agents
        client_agent1.stop_agent()
        agent1.stop_agent()
        agent2.stop_agent()
        agent3.stop_agent()
        agent4.stop_agent()
        agent5.stop_agent()
