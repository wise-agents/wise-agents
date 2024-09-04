import os
import threading

from wiseagents import WiseAgentMessage, WiseAgentRegistry
from wiseagents.agents import LLMOnlyWiseAgent, PassThroughClientAgent, SequentialCoordinatorWiseAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport

cond = threading.Condition()


def response_delivered(message: WiseAgentMessage):
    with cond:
        response = message.message
        assert "Farah" in response
        assert "Agent1" in response
        assert "Agent2" in response
        print(f"C Response delivered: {response}")
        cond.notify()


def test_sequential_coordinator():
    """
    Requires STOMP_USER and STOMP_PASSWORD.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    llm1 = OpenaiAPIWiseAgentLLM(system_message="Your name is Agent1. Answer my greeting saying Hello and my name and tell me your name.",
                                 model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                 api_key=groq_api_key)
    agent1 = LLMOnlyWiseAgent(name="Agent1", description="This is a test agent", llm=llm1,
                              trasport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Agent1"))

    llm2 = OpenaiAPIWiseAgentLLM(system_message="Your name is Agent2. Answer my greeting saying Hello and include all names from the given message and tell me your name.",
                                 model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                 api_key=groq_api_key)
    agent2 = LLMOnlyWiseAgent(name="Agent2", description="This is a test agent", llm=llm2,
                              trasport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Agent2"))

    coordinator = SequentialCoordinatorWiseAgent(name="SequentialCoordinator", description="This is a coordinator agent",
                                                 transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="SequentialCoordinator"),
                                                 agents=["Agent1", "Agent2"])

    with cond:
        client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1", description="This is a test agent",
                                               transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                               )
        client_agent1.set_response_delivery(response_delivered)
        client_agent1.send_request(WiseAgentMessage("My name is Farah", "PassThroughClientAgent1"),
                                   "SequentialCoordinator")
        cond.wait()

        for agent in WiseAgentRegistry.get_agents():
            print(f"Agent: {agent}")
        for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
            print(f'{message.sender} : {message.message} ')
