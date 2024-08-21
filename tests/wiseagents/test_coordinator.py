import os
import threading

from wiseagents import WiseAgentMessage, WiseAgentRegistry
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport
from wiseagents.wise_agent_impl import CollaboratorWiseAgent, CoordinatorWiseAgent, PassThroughClientAgent

cond = threading.Condition()


def final_response_delivered(message: WiseAgentMessage):
    with cond:
        response = message.message
        assert response
        print(f"C Response delivered: {response}")
        cond.notify()


def test_coordinator():
    """
    Requires STOMP_USER, STOMP_PASSWORD, and a Groq API_KEY.
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    llm1 = OpenaiAPIWiseAgentLLM(system_message="You will be coordinating a group of agents to solve a problem.",
                                 model_name="llama-3.1-70b-versatile",
                                 remote_address="https://api.groq.com/openai/v1",
                                 api_key=groq_api_key)
    agent1 = CoordinatorWiseAgent(name="Coordinator", description="This is a coordinator agent", llm=llm1,
                                  transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Coordinator"),
                                  phases=["Information Gathering", "Verification of Information", "Analysis"],
                                  max_iterations=2)

    llm4 = OpenaiAPIWiseAgentLLM(system_message="You are a helpful assistant that will provide information about the given error message",
                                 model_name="llama-3.1-70b-versatile",
                                 remote_address="https://api.groq.com/openai/v1",
                                 api_key=groq_api_key)
    agent4 = CollaboratorWiseAgent(name="Agent4", description="This agent provides information about error messages using Source1", llm=llm4,
                                   transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                     agent_name="Agent4"))

    llm5 = OpenaiAPIWiseAgentLLM(system_message="You are a helpful assistant that will provide information about the given error message",
                                 model_name="llama-3.1-70b-versatile",
                                 remote_address="https://api.groq.com/openai/v1",
                                 api_key=groq_api_key)
    agent5 = CollaboratorWiseAgent(name="Agent5", description="This agent provides information about error messages using Source2",
                                   llm=llm5,
                                   transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                     agent_name="Agent5"))

    llm6 = OpenaiAPIWiseAgentLLM(system_message="You are a helpful assistant that will determine the underlying cause of a problem given information about the problem",
                                 model_name="llama-3.1-70b-versatile",
                                 remote_address="https://api.groq.com/openai/v1",
                                 api_key=groq_api_key)
    agent6 = CollaboratorWiseAgent(name="Agent6",
                              description="This agent describes the underlying cause of a problem given information about the problem. This agent" + 
                                          " should be called after getting information about the problem using Agent4 or Agent5.",
                              llm=llm6,
                              transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                               agent_name="Agent6"))

    llm7 = OpenaiAPIWiseAgentLLM(system_message="You will determine if the information provided by other agents is accurate.",
                                 model_name="llama-3.1-70b-versatile",
                                 remote_address="https://api.groq.com/openai/v1",
                                 api_key=groq_api_key)
    agent7 = CollaboratorWiseAgent(name="Agent7",
                                   description="This agent is used to verify if the information provided by other agents is accurate. This " +
                                               "agent should be called after getting information about a problem using Agent4 or Agent5. This agent " +
                                               "should be called before calling Agent6.",
                                   llm=llm7,
                                   transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                     agent_name="Agent7"))

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