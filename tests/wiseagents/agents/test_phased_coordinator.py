import os
import threading

import pytest

from wiseagents import WiseAgentMessage, WiseAgentRegistry
from wiseagents.agents import CollaboratorWiseAgent, PassThroughClientAgent, PhasedCoordinatorWiseAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport

cond = threading.Condition()


@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield
    WiseAgentRegistry.clear_agents()
    WiseAgentRegistry.clear_contexts()

def final_response_delivered(message: WiseAgentMessage):
    with cond:
        response = message.message
        assert response
        print(f"C Response delivered: {response}")
        cond.notify()


def test_phased_coordinator():
    """
    Requires STOMP_USER, STOMP_PASSWORD, and a Groq API_KEY.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")

    llm = OpenaiAPIWiseAgentLLM(system_message="You are a helpful assistant.",
                                model_name="llama-3.1-70b-versatile",
                                remote_address="https://api.groq.com/openai/v1",
                                api_key=groq_api_key)

    agent1 = PhasedCoordinatorWiseAgent(name="Coordinator", description="This is a coordinator agent", llm=llm,
                                  transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Coordinator"),
                                  phases=["Information Gathering", "Verification of Information", "Analysis"],
                                  system_message="You will be coordinating a group of agents to solve a problem.",
                                  max_iterations=2)

    agent2 = CollaboratorWiseAgent(name="Agent2", description="This agent provides information about error messages using Source1", llm=llm,
                                   transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                     agent_name="Agent2"),
                                   system_message="You are a helpful assistant that will provide information about the given error message")

    agent3 = CollaboratorWiseAgent(name="Agent3", description="This agent provides information about error messages using Source2",
                                   llm=llm,
                                   transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                     agent_name="Agent3"),
                                   system_message="You are a helpful assistant that will provide information about the given error message")

    agent4 = CollaboratorWiseAgent(name="Agent4",
                                   description="This agent describes the underlying cause of a problem given information about the problem. This agent" +
                                               " should be called after getting information about the problem using Agent2 or Agent3.",
                                   llm=llm,
                                   transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                     agent_name="Agent4"),
                                   system_message="You are a helpful assistant that will determine the underlying cause of a problem given information about the problem")

    agent5 = CollaboratorWiseAgent(name="Agent5",
                                   description="This agent is used to verify if the information provided by other agents is accurate. This " +
                                               "agent should be called after getting information about a problem using Agent2 or Agent3. This agent " +
                                               "should be called before calling Agent4.",
                                   llm=llm,
                                   transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                     agent_name="Agent5"),
                                   system_message="You will determine if the information provided by other agents is accurate.")

    with cond:
        client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1", description="This is a test agent",
                                               transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                               )
        client_agent1.set_response_delivery(final_response_delivered)
        client_agent1.send_request(WiseAgentMessage("How do I prevent the following exception from occurring:"
                                                    "Exception Details: java.lang.NullPointerException at com.example.ExampleApp.processData(ExampleApp.java:47)", 
                                                    "PassThroughClientAgent1"),
                                   "Coordinator")
        cond.wait()

        for agent in WiseAgentRegistry.get_agents():
            print(f"Agent: {agent}")
        for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
            print(f'{message.sender} : {message.message} ')