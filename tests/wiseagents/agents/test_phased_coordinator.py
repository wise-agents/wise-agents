import logging
import os
import threading
import traceback

import pytest

from wiseagents import WiseAgentMessage, WiseAgentMetaData, WiseAgentRegistry
from wiseagents.agents import LLMOnlyWiseAgent, PassThroughClientAgent, \
    PhasedCoordinatorWiseAgent
from wiseagents.llm import OpenaiAPIWiseAgentLLM
from wiseagents.transports import StompWiseAgentTransport
from tests.wiseagents import assert_standard_variables_set, mock_open_ai_for_ci, mock_open_ai_chat_completion, \
    get_user_messages, get_system_messages, get_assistant_messages

cond = threading.Condition()
assertError : AssertionError = None

@pytest.fixture(scope="session", autouse=True)
def run_after_all_tests():
    assert_standard_variables_set()
    yield


logger = logging.getLogger(__name__)
lock = threading.RLock()

agent_invocation = 0


def _assert(cur_invocation, condition: bool, message: str = None):
    # Report assertions at the end. If we do it here we hang
    global assertError
    if assertError:
        # Only store the first assertError
        return
    if not condition:
        try:
            if message:
                assert condition, message
            else:
                assert condition
        except AssertionError as e:
            logging.info(f"Assertion failed for invocation {cur_invocation} {e}. See traceback section for more details.")
            traceback.print_exc()
            traceback.print_stack()
            assertError = e
            with cond:
                cond.notify()

def final_response_delivered(message: WiseAgentMessage):
    global  assertError
    with cond:
        response = message.message
        try:
            assert response
            print(f"C Response delivered: {response}")
        except AssertionError as e:
            logging.info(f"assertion failed ")
            assertError = e
        cond.notify()



def _check_messages(cur_invocation, size: int, type: str, messages: list):
    _assert(cur_invocation, len(messages) >= size, f"Unexpected {type} messages received by the Mock LLM {messages}")


def _check_agent_is_in_message(cur_invocation, agent_name: str, agent_desc: str, message: str):
    _assert(cur_invocation, f"Agent Name: {agent_name} Agent Description: {agent_desc}" in message)

def _increment_and_get_agent_invocation() -> int:
    global agent_invocation
    with lock:
        agent_invocation += 1
        return agent_invocation


def _mock_llm(*args, **kwargs):
    cur_invocation = _increment_and_get_agent_invocation()
    logging.debug(f"TEST: Current invocation: {cur_invocation}")
    try:
        messages = kwargs["messages"]

        # Should have at least a system and a user message
        _assert(cur_invocation, len(messages) > 1, f"Unexpected messages received by the Mock LLM {messages}")
        system_messages = get_system_messages(messages)
        user_messages = get_user_messages(messages)
        assistant_messages = get_assistant_messages(messages)

        ############################################################################
        # Checks for the first query received, the history will be maintained for the future queries
        _check_messages(cur_invocation, 1, "system", system_messages)
        _assert(cur_invocation, system_messages[0] == "You will be coordinating a group of agents to solve a problem.")
        _check_messages(cur_invocation, 1, "user", user_messages)
        _assert(cur_invocation,
                "determine all of the agents that could be required to solve the query" in user_messages[0])
        _assert(cur_invocation, "How do I prevent the following exception" in user_messages[0])
        _assert(cur_invocation, "NullPointerException" in user_messages[0])
        _assert(cur_invocation, "Available agents:" in user_messages[0])
        _check_agent_is_in_message(cur_invocation, "Coordinator", "This is a coordinator agent", user_messages[0])
        _check_agent_is_in_message(cur_invocation, "PassThroughClientAgent1", "This is a test agent", user_messages[0])
        _check_agent_is_in_message(cur_invocation, "Agent2",
                                   "This agent provides information about error messages using Source1",
                                   user_messages[0])
        _check_agent_is_in_message(cur_invocation, "Agent3",
                                   "This agent provides information about error messages using Source2",
                                   user_messages[0])
        _check_agent_is_in_message(cur_invocation, "Agent4",
                                   "This agent describes the underlying cause of a problem given information about the problem. "
                                   "This agent should be called after getting information about the problem using Agent2 or Agent3.",
                                   user_messages[0])
        _check_agent_is_in_message(cur_invocation, "Agent5",
                                   "This agent is used to verify if the information provided by other agents is accurate. "
                                   "This agent should be called after getting information about a problem using Agent2 or Agent3. "
                                   "This agent should be called before calling Agent4.", user_messages[0])
        _check_messages(cur_invocation, 0, "assistant", assistant_messages)

        if cur_invocation == 1:
            _assert(cur_invocation, len(messages) == 2, f"Unexpected messages received by the Mock "
                                                        f"LLM {messages} for invocation {cur_invocation}")
            return mock_open_ai_chat_completion("Agent2 Agent3 Agent5 Agent4")

        ############################################################################
        # Checks for the second query received
        _check_messages(cur_invocation, 4, "all", messages)

        _check_messages(cur_invocation, 1, "system", system_messages)
        # System messages have not changed, no need to check again

        _check_messages(cur_invocation, 1, "assistant", assistant_messages)
        # The assistant message here will be what was returned by the previous step
        _assert(cur_invocation, assistant_messages[0] == "Agent2 Agent3 Agent5 Agent4")

        _check_messages(cur_invocation, 2, "user", user_messages)
        # Check the new user message.
        _assert(cur_invocation,
                "Assign each of the agents that will be required to solve the query to" in user_messages[1])
        _assert(cur_invocation, "Information Gathering, Verification of Information, Analysis" in user_messages[1])

        if cur_invocation == 2:
            _assert(cur_invocation, len(messages) == 4, f"Unexpected messages received by the Mock "
                                                        f"LLM {messages} for invocation {cur_invocation}")
            return mock_open_ai_chat_completion("Agent2 Agent3\nAgent5\nAgent4")

        ############################################################################
        # Checks for the third and fourth queries received
        # These will be for Agent2 and Agent3.
        _check_messages(cur_invocation, 7, "all", messages)

        _check_messages(cur_invocation, 3, "user", user_messages)
        # Check the new user message
        if not cur_invocation == 7:
            _assert(cur_invocation, user_messages[2] ==
                    "How do I prevent the following exception from occurring:Exception Details: "
                    "java.lang.NullPointerException at com.example.ExampleApp.processData(ExampleApp.java:47)")

        _check_messages(cur_invocation, 2, "assistant", assistant_messages)
        # The new assistant message here will be what was returned by the previous step
        _assert(cur_invocation, assistant_messages[1] == "Agent2 Agent3\nAgent5\nAgent4")

        if cur_invocation == 3 or cur_invocation == 4:
            # For the fourth query, we might have an additional message from the assistant. The two queries run
            # in parallel on different agents, so it depends on the timing
            _assert(cur_invocation, (cur_invocation == 3 and len(messages) == 7) or
                    cur_invocation == 4 and len(messages) in (7, 8))

            _check_messages(cur_invocation, 2, "system", system_messages)
            # Check the new system message
            _assert(cur_invocation, system_messages[1] ==
                    "You are a helpful assistant that will provide information about the given error message")

            if cur_invocation == 3:
                return mock_open_ai_chat_completion("It is important to initialise all variables!")
            elif cur_invocation == 4:
                return mock_open_ai_chat_completion("Check if a variable is null before using it.")

        ############################################################################
        # This is the stage with Agent 5
        # This will be the fifth query received
        _check_messages(cur_invocation, 9, "all", messages)

        _check_messages(cur_invocation, 4, "assistant", assistant_messages)
        _assert(cur_invocation, assistant_messages[1] == "Agent2 Agent3\nAgent5\nAgent4")
        latest_assistant_messages = assistant_messages[2:4]
        _assert(cur_invocation, "It is important to initialise all variables!" in latest_assistant_messages)
        _assert(cur_invocation, "Check if a variable is null before using it." in latest_assistant_messages)

        _check_messages(cur_invocation, 3, "user", user_messages)
        # user messages are the same as earlier
        if cur_invocation == 5:
            _assert(cur_invocation, system_messages[1] ==
                    "You will determine if the information provided by other agents is accurate.")
            _assert(cur_invocation, len(messages) == 9)
            _check_messages(cur_invocation, 2, "system", system_messages)
            _assert(cur_invocation,
                    system_messages[1] == "You will determine if the information provided by other agents is accurate.")
            return mock_open_ai_chat_completion("It seems to avoid an NPE you should "
                                                "take care to initialise variables and check they are set before use.")

        ############################################################################
        # This is the stage with Agent 4
        # This will be the sixth query received

        _check_messages(cur_invocation, 5, "assistant", assistant_messages)
        _assert(cur_invocation, assistant_messages[4] == "It seems to avoid an NPE you should "
                                                         "take care to initialise variables and check they are set before use.")

        if cur_invocation == 6:
            _assert(cur_invocation, len(messages) == 10, messages)
            _check_messages(cur_invocation, 2, "system", system_messages)
            _assert(cur_invocation,
                    system_messages[1] == "You are a helpful assistant that will determine the underlying cause of "
                                          "a problem given information about the problem")
            return mock_open_ai_chat_completion("Look at line 47 of ExampleApp.java and check if the "
                                                "object is initialised before using it.")

        if cur_invocation == 7:
            _assert(cur_invocation, len(messages) == 10, messages)
            _check_messages(cur_invocation, 5, "assistant", assistant_messages)
            _assert(cur_invocation, assistant_messages[5] == "Look at line 47 of ExampleApp.java and check if the "
                                                             "object is initialised before using it.")
            _assert(cur_invocation, user_messages[2] ==
                    "What is the final answer for the original query? Provide the answer followed by "
                    "a confidence score from 0 to 100 to indicate how certain you are of the answer. "
                    "Format the response with just the answer first followed by just the confidence "
                    "score on the next line. For example:\n Your answer goes here.\n 85\n")

            return mock_open_ai_chat_completion(
                "To prevent the NullPointerException from occurring, ensure that all variables are properly initialized "
                "before using them and that any objects passed to the processData method are properly instantiated. "
                "Consider explicitly initializing objects before use, using Optional in Java, avoiding autoboxing, "
                "and adding null checks to prevent attempts to call methods on null objects.\n\n 95")

        _assert(cur_invocation, False, f"Unexpected messages received by the Mock LLM {user_messages}")
    except Exception as e:
        logging.error(f"Error - Current invocation: {cur_invocation}: {e}")
        raise e
    finally:
        logging.debug(f"TEST - END: Current invocation: {cur_invocation}")


def test_phased_coordinator(mocker):
    """
    Requires STOMP_USER, STOMP_PASSWORD, and a Groq API_KEY.
    """
    mock_open_ai_for_ci(mocker, _mock_llm)
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
        WiseAgentRegistry.create_context("default")
        with cond:
            client_agent1 = PassThroughClientAgent(name="PassThroughClientAgent1", metadata=WiseAgentMetaData(description="This is a test agent"),
                                                   transport=StompWiseAgentTransport(host='localhost', port=61616, agent_name="PassThroughClientAgent1")
                                                   )
            client_agent1.set_response_delivery(final_response_delivered)
            client_agent1.send_request(WiseAgentMessage(message= "How do I prevent the following exception from occurring:"
                                                        "Exception Details: java.lang.NullPointerException at com.example.ExampleApp.processData(ExampleApp.java:47)",
                                                        sender="PassThroughClientAgent1", context_name="default"),
                                       "Coordinator")
            cond.wait(timeout=300)
            if assertError is not None:
                logging.info(f"assertion failed")
                raise assertError

            logging.debug(f"registered agents= {WiseAgentRegistry.fetch_agents_metadata_dict()}")
            for message in WiseAgentRegistry.get_context('default').message_trace:
                logging.debug(f'{message}')
    finally:
        #stop agents
        client_agent1.stop_agent()
        agent1.stop_agent()
        agent2.stop_agent()
        agent3.stop_agent()
        agent4.stop_agent()
        agent5.stop_agent()
        WiseAgentRegistry.remove_context("default")
