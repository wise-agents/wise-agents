import logging
import os
import threading
from typing import List, Optional

import pytest
from openai.types.chat import ChatCompletionMessageParam

from wiseagents import WiseAgent, WiseAgentEvent, WiseAgentMessage, WiseAgentMetaData, WiseAgentRegistry, \
    WiseAgentTransport
from wiseagents.agents import LLMOnlyWiseAgent, PassThroughClientAgent, SequentialCoordinatorWiseAgent, \
    SequentialMemoryCoordinatorWiseAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM, WiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport

cond1 = threading.Condition()
cond2 = threading.Condition()

assertError : AssertionError = None

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    yield


class FinalWiseAgent(WiseAgent):

    def __init__(self, name: str, metadata: WiseAgentMetaData, transport: WiseAgentTransport, llm: WiseAgentLLM):
        self._max_iterations = 2
        super().__init__(name=name, metadata=metadata, transport=transport, llm=llm)

    def process_request(self, request: WiseAgentMessage,
                        conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
        conversation_history.append(
            {"role": "system", "content": self.metadata.system_message or self.llm.system_message})
        conversation_history.append({"role": "user", "content": request.message})
        llm_response = self.llm.process_chat_completion(conversation_history, [])
        ctx = WiseAgentRegistry.get_or_create_context(request.context_name)
        ctx.append_chat_completion(chat_uuid=request.chat_id, messages=llm_response.choices[0].message)
        if len(ctx.get_queries(request.chat_id)) < self._max_iterations:
            ctx.add_query(request.chat_id, "Atlanta")
            ctx.set_restart_sequence(request.chat_id, True)
        return llm_response.choices[0].message.content

    def process_response(self, response: WiseAgentMessage):
        pass

    def process_event(self, event: WiseAgentEvent):
        pass

    def process_error(self, error: WiseAgentMessage):
        pass


def response_delivered(message: WiseAgentMessage):
    global assertError
    with cond1:
        response = message.message

        try:
            assert "Agent0" in response
            assert "Agent1" in response
            assert "Agent2" in response
        except AssertionError:
            logging.info(f"assertion failed")
            assertError = AssertionError
        cond1.notify()
        
def response_delivered_restart(message: WiseAgentMessage):
    global assertError
    with cond2:
        response = message.message

        try:
            assert "Raleigh" in response
            assert "North Carolina" in response
            assert "Atlanta" in response
            assert "Georgia" in response
        except AssertionError:
            logging.info(f"assertion failed")
            assertError = AssertionError
        cond2.notify()


def test_sequential_coordinator():
    """
    Requires STOMP_USER and STOMP_PASSWORD.
    """
    try:
        global assertError
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        llm1 = OpenaiAPIWiseAgentLLM(system_message="Your name is Agent1. Answer my greeting saying Hello and my name and tell me your name.",
                                    model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                    api_key=groq_api_key)
        agent1 = LLMOnlyWiseAgent(name="Agent1", metadata=WiseAgentMetaData(description="This is a test agent"), llm=llm1,
                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Agent1"))

        llm2 = OpenaiAPIWiseAgentLLM(system_message="Your name is Agent2. Answer my greeting saying Hello and include all agent names from the given message and tell me your name.",
                                    model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
                                    api_key=groq_api_key)
        agent2 = LLMOnlyWiseAgent(name="Agent2", metadata=WiseAgentMetaData(description="This is a test agent"), llm=llm2,
                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="Agent2"))

        coordinator = SequentialCoordinatorWiseAgent(name="SequentialCoordinator", metadata=WiseAgentMetaData(description="This is a coordinator agent"),
                                                    transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="SequentialCoordinator"),
                                                    agents=["Agent1", "Agent2"])

        with cond1:
            client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1", metadata=WiseAgentMetaData(description="This is a test agent"),
                                                transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                )
            client_agent1.set_response_delivery(response_delivered)
            client_agent1.send_request(WiseAgentMessage("My name is Agent0", "PassThroughClientAgent1"),
                                    "SequentialCoordinator")
            cond1.wait()
            if assertError is not None:
                logging.info(f"assertion failed")
                raise assertError
            logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")
            for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
                logging.debug(f'{message}')
    finally:
        #stop all agents
        client_agent1.stop_agent()
        agent1.stop_agent()
        agent2.stop_agent()
        coordinator.stop_agent()


def test_sequential_memory_coordinator_restart_sequence():
    """
    Requires STOMP_USER and STOMP_PASSWORD.
    """
    try:
        global assertError
        groq_api_key = os.getenv("GROQ_API_KEY")

        llm1 = OpenaiAPIWiseAgentLLM(
            system_message="Given a city, tell me what state the city is in. If we discussed other cities and states, include them in the response.",
            model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
            api_key=groq_api_key)
        agent1 = LLMOnlyWiseAgent(name="AgentOne", metadata=WiseAgentMetaData(description="This is a test agent"),
                                  llm=llm1,
                                  transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="AgentOne"))

        llm2 = OpenaiAPIWiseAgentLLM(
            system_message="Given a city and state, tell me what country the state is in." +
                           " If we discussed other cities and states, include them in the response.",
            model_name="llama-3.1-70b-versatile", remote_address="https://api.groq.com/openai/v1",
            api_key=groq_api_key)
        agent2 = FinalWiseAgent(name="AgentTwo", metadata=WiseAgentMetaData(description="This is a test agent"),
                                  llm=llm2,
                                  transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="AgentTwo"))

        coordinator = SequentialMemoryCoordinatorWiseAgent(name="SequentialMemoryCoordinator", metadata=WiseAgentMetaData(
            description="This is a coordinator agent", system_message="You are a helpful assistant"),
                                                           transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                                             agent_name="SequentialMemoryCoordinator"),
                                                           agents=["AgentOne", "AgentTwo"])

        with cond2:
            client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1",
                                                   metadata=WiseAgentMetaData(description="This is a test agent"),
                                                   transport=StompWiseAgentTransport(host='localhost', port=61616,
                                                                                     agent_name="PassThroughClientAgent1")
                                                   )
            client_agent1.set_response_delivery(response_delivered_restart)
            client_agent1.send_request(WiseAgentMessage("Raleigh", "PassThroughClientAgent1"),
                                       "SequentialMemoryCoordinator")
            cond2.wait()
            if assertError is not None:
                logging.info(f"assertion failed")
                raise assertError
            logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")
            for message in WiseAgentRegistry.get_or_create_context('default').message_trace:
                logging.debug(f'{message}')
    finally:
        # stop all agents
        client_agent1.stop_agent()
        agent1.stop_agent()
        agent2.stop_agent()
        coordinator.stop_agent()
