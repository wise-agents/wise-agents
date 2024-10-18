import logging
import uuid
from typing import Callable, List, Optional

from wiseagents import WiseAgent, WiseAgentCollaborationType, WiseAgentMessage, WiseAgentMessageType, WiseAgentMetaData, WiseAgentRegistry, WiseAgentTransport
from wiseagents.llm import WiseAgentLLM

CONFIDENCE_SCORE_THRESHOLD = 85
MAX_ITERATIONS_FOR_COORDINATOR = 5
CANNOT_ANSWER = "I don't know the answer to the query."

class SequentialCoordinatorWiseAgent(WiseAgent):
    """
    This agent will coordinate the execution of a sequence of agents.
    Use Stomp protocol.
    """
    yaml_tag = u'!wiseagents.agents.SequentialCoordinatorWiseAgent'

    
    def __init__(self, name: str, metadata: WiseAgentMetaData, transport: WiseAgentTransport, agents: List[str]):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            transport (WiseAgentTransport): the transport to use for communication
            agents (List[str]): the list of agents to coordinate
        """
        self._name = name
        self._agents = agents
        super().__init__(name=name, metadata=metadata, transport=transport, llm=None)

    def __repr__(self):
        """Return a string representation of the agent."""
        return f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, agents={self.agents})"

    def handle_request(self, request):
        """
        Process a request message by passing it to the first agent in the sequence.

        Args:
            request (WiseAgentMessage): the request message to process
        """
        logging.debug(f"Sequential coordinator received request: {request}")

        # Generate a chat ID that will be used to collaborate on this query
        sub_ctx_name = f'{self.name}.{str(uuid.uuid4())}'

        ctx = WiseAgentRegistry.create_sub_context(request.context_name, sub_ctx_name)
        ctx.set_collaboration_type(WiseAgentCollaborationType.SEQUENTIAL)
        ctx.set_agents_sequence(self._agents)
        ctx.set_route_response_to(request.sender)
        self.send_request(WiseAgentMessage(message=request.message, sender=self.name, context_name=ctx.name), self._agents[0])

    def process_response(self, response):
        """
        Process a response message by passing it to the next agent in the sequence.

        Args:
            response (WiseAgentMessage): the response message to process
        """
        if response.message:
            raise ValueError(f"Unexpected response message: {response.message}")
        return True

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def stop(self):
        """Do nothing"""
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def agents(self) -> List[str]:
        """Get the list of agents."""
        return self._agents

    @property
    def response_delivery(self) -> Optional[Callable[[], WiseAgentMessage]]:
        """
        Get the function to deliver the response to the client.

        Returns:
            (Callable[[], WiseAgentMessage]): the function to deliver the response to the client
        """
        return self._response_delivery

    def set_response_delivery(self, response_delivery: Callable[[], WiseAgentMessage]):
        """Set the function to deliver the response to the client."""
        self._response_delivery = response_delivery

class SequentialMemoryCoordinatorWiseAgent(WiseAgent):
    yaml_tag = u'!wiseagents.agents.SequentialMemoryCoordinatorWiseAgent'

    def __init__(self, name: str, metadata: WiseAgentMetaData, transport: WiseAgentTransport, agents: List[str]):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            transport (WiseAgentTransport): the transport to use for communication
            agents (List[str]): the list of agents to coordinate
        """
        self._name = name
        self._agents = agents
        super().__init__(name=name, metadata=metadata, transport=transport, llm=None)

    def __repr__(self):
        """Return a string representation of the agent."""
        return f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, agents={self.agents})"


    def handle_request(self, request):
        """
        Process a request message by passing it to the first agent in the sequence.

        Args:
            request (WiseAgentMessage): the request message to process
        """
        logging.getLogger(self.name).info(f"Received a message from {request.sender}. Starting to kick off the sequence of agents")

        # Generate a chat ID that will be used to collaborate on this query
        sub_ctx_name = f'{self.name}.{str(uuid.uuid4())}'

        ctx = WiseAgentRegistry.create_sub_context(request.context_name, sub_ctx_name)
        ctx.set_collaboration_type(WiseAgentCollaborationType.SEQUENTIAL_MEMORY)
        if self.metadata.system_message:
            ctx.append_chat_completion(messages={"role": "system", "content": self.metadata.system_message})

        ctx.set_agents_sequence(self._agents)
        ctx.set_route_response_to(request.sender)
        ctx.add_query(request.message)
        self.send_request(WiseAgentMessage(message=request.message, sender=self.name, context_name=ctx.name), self._agents[0])


class PhasedCoordinatorWiseAgent(WiseAgent):
    """
    This agent will coordinate the execution of a group of agents in order to determine the response
    to a query. The agents will be executed in phases, where agents within a phase will be executed
    in parallel. After the phases have completed, the coordinator may choose to repeat the phases
    until it is satisfied with the final response or determines it's not possible to answer the query.
    """
    yaml_tag = u'!wiseagents.agents.PhasedCoordinatorWiseAgent'

    def __new__(cls, *args, **kwargs):
        """Create a new instance of the class, setting default values for the instance variables."""
        obj = super().__new__(cls)
        obj._phases = ["Data Collection", "Data Analysis"]
        obj._max_iterations = MAX_ITERATIONS_FOR_COORDINATOR
        obj._confidence_score_threshold = CONFIDENCE_SCORE_THRESHOLD
        return obj

    def __init__(self, name: str, metadata: WiseAgentMetaData, transport: WiseAgentTransport, llm: WiseAgentLLM,
                 phases: Optional[List[str]] = None, max_iterations: Optional[int] = MAX_ITERATIONS_FOR_COORDINATOR,
                 confidence_score_threshold: Optional[int] = CONFIDENCE_SCORE_THRESHOLD):
        """
        Initialize the agent.

        Args:
            name (str): the name of the agent
            metadata (WiseAgentMetaData): the metadata for the agent
            transport (WiseAgentTransport): the transport to use for communication
            llm (WiseAgentLLM): the LLM to use for coordinating the collaboration
            phases (Optional[List[str]]): the optional list of phase names, defaults to "Data Collection" and "Data Analysis"
            max_iterations (Optional[int]): the maximum number of iterations to run the phases, defaults to 5
            confidence_score_threshold (Optional[int]): the confidence score threshold to determine if the final answer
            is acceptable, defaults to 85
        """
        self._name = name
        self._phases = phases if phases is not None else ["Data Collection", "Data Analysis"]
        self._max_iterations = max_iterations
        self._confidence_score_threshold = confidence_score_threshold
        super().__init__(name=name, metadata=metadata, transport=transport, llm=llm)

    def __repr__(self):
        """Return a string representation of the agent."""
        return (f"{self.__class__.__name__}(name={self.name}, metadata={self.metadata}, transport={self.transport},"
                f"llm={self.llm}, phases={self.phases},max_iterations={self.max_iterations}")

    @property
    def phases(self) -> List[str]:
        """Get the list of phases."""
        return self._phases

    @property
    def max_iterations(self) -> int:
        """Get the maximum number of iterations."""
        return self._max_iterations

    @property
    def confidence_score_threshold(self) -> int:
        """Get the confidence score threshold."""
        return self._confidence_score_threshold

    def handle_request(self, request):
        """
        Process a request message by kicking off the collaboration in phases.

        Args:
            request (WiseAgentMessage): the request message to process
        """
        logging.debug(f"Coordinator received request: {request}")

        # Generate a chat ID that will be used to collaborate on this query
        sub_ctx_name = f'{self.name}.{str(uuid.uuid4())}'

        ctx = WiseAgentRegistry.create_sub_context(request.context_name, sub_ctx_name)
        ctx.set_collaboration_type(WiseAgentCollaborationType.PHASED)
        ctx.set_route_response_to(request.sender)
        logging.debug(f"Registred context: {WiseAgentRegistry.get_context(ctx.name)}")
        # Determine the agents required to answer the query
        agent_selection_prompt = ("Given the following query and a description of the agents that are available," +
                                  " determine all of the agents that could be required to solve the query." +
                                  " Format the response as a space separated list of agent names and don't include " +
                                  " anything else in the response.\n" +
                                  " Query: " + request.message + "\n" + "Available agents:\n" +
                                  "\n".join(WiseAgentRegistry.get_agent_names_and_descriptions()) + "\n")
        if self.metadata.system_message or self.llm.system_message:
            ctx.append_chat_completion(messages={"role": "system", "content": self.metadata.system_message or self.llm.system_message})
        ctx.append_chat_completion(messages={"role": "user", "content": agent_selection_prompt})

        logging.debug(f"messages: {ctx.llm_chat_completion}")
        llm_response = self.llm.process_chat_completion(ctx.llm_chat_completion, tools=[])
        msg = {"content": llm_response.choices[0].message.content, "role": "assistant"}
        ctx.append_chat_completion(messages=msg)

        # Assign the agents to phases
        agent_assignment_prompt = ("Assign each of the agents that will be required to solve the query to one of the following phases:\n" +
                                   ", ".join(self.phases) + "\n" +
                                   "Assume that agents within a phase will be executed in parallel." +
                                   " Format the response as a space separated list of agents for each phase, where the first"
                                   " line contains the list of agents for the first phase and second line contains the list of"
                                   " agents for the second phase and so on. Don't include anything else in the response.\n")
        ctx.append_chat_completion(messages={"role": "user", "content": agent_assignment_prompt})
        llm_response = self.llm.process_chat_completion(ctx.llm_chat_completion, tools=[])
        msg = {"content": llm_response.choices[0].message.content, "role": "assistant"}
        ctx.append_chat_completion(messages=msg)
        phases = [phase.split() for phase in llm_response.choices[0].message.content.splitlines()]
        ctx.set_agent_phase_assignments(phases)
        ctx.set_current_phase(0)
        ctx.add_query(request.message)

        # Kick off the first phase
        for agent in phases[0]:
            self.send_request(WiseAgentMessage(message=request.message, sender=self.name,
                                               context_name=ctx.name), agent)

    def process_response(self, response : WiseAgentMessage):
        """
        Process a response message. If this message is from the last agent remaining in the current phase, then
        kick off the next phase of collaboration if there are more phases. Otherwise, determine if we should
        return the final answer or if we need to go back to the first phase and repeat with a rephrased query.

        Args:
            response (WiseAgentMessage): the response message to process
        """
        ctx = WiseAgentRegistry.get_context(response.context_name)
        
        if response.message_type != WiseAgentMessageType.ACK:
            raise ValueError(f"Unexpected response message_type: {response.message_type} with message: {response.message}")

        # Remove the agent from the required agents for this phase
        ctx.remove_required_agent_for_current_phase(response.sender)

        # If there are no more agents remaining in this phase, move on to the next phase,
        # return the final answer, or iterate
        if len(ctx.get_required_agents_for_current_phase()) == 0:
            next_phase = ctx.get_agents_for_next_phase()
            if next_phase is None:
                # Determine the final answer
                final_answer_prompt = ("What is the final answer for the original query? Provide the answer followed" +
                                       " by a confidence score from 0 to 100 to indicate how certain you are of the" +
                                       " answer. Format the response with just the answer first followed by just" +
                                       " the confidence score on the next line. For example:\n" +
                                       " Your answer goes here.\n"
                                       " 85\n")
                ctx.append_chat_completion(messages={"role": "user", "content": final_answer_prompt})
                llm_response = self.llm.process_chat_completion(ctx.llm_chat_completion, tools=[])
                final_answer_and_score = llm_response.choices[0].message.content.splitlines()
                final_answer = "\n".join(final_answer_and_score[:-1])
                if final_answer_and_score[-1].strip().isnumeric():
                    score = int(final_answer_and_score[-1])
                else:
                    # A score could not be determined
                    score = 0

                # Determine if we should return the final answer or iterate
                if score >= self.confidence_score_threshold:
                    self.send_response(WiseAgentMessage(message=final_answer, sender=self.name,
                                                        context_name=response.context_name), ctx.get_route_response_to())
                elif len(ctx.get_queries()) == self.max_iterations:
                    self.send_response(WiseAgentMessage(message=CANNOT_ANSWER, message_type=WiseAgentMessageType.CANNOT_ANSWER,
                                                        sender=self.name, context_name=response.context_name),
                                       ctx.get_route_response_to())
                else:
                    # Rephrase the query and iterate
                    if len(ctx.get_queries()) < self.max_iterations:
                        rephrase_query_prompt = ("The final answer was not considered good enough to respond to the original query.\n" +
                                                 " The original query was: " + ctx.get_queries()[0] + "\n" +
                                                 " Your task is to analyze the original query for its intent along with the conversation" +
                                                 " history and final answer to rephrase the original query to yield a better final answer." +
                                                 " The response should contain only the rephrased query."
                                                 " Don't include anything else in the response.\n")
                        ctx.append_chat_completion(messages={"role": "user", "content": rephrase_query_prompt})
                        # Note that llm_chat_completion is being used here so we have the full history
                        llm_response = self.llm.process_chat_completion(ctx.llm_chat_completion, tools=[])
                        rephrased_query = llm_response.choices[0].message.content
                        ctx.append_chat_completion(messages=llm_response.choices[0].message)
                        ctx.set_current_phase(0)
                        ctx.add_query(rephrased_query)
                        for agent in ctx.get_required_agents_for_current_phase():
                            self.send_request(WiseAgentMessage(message=rephrased_query, sender=self.name,
                                                               context_name=response.context_name),
                                              agent)
            else:
                # Kick off the next phase
                for agent in next_phase:
                    self.send_request(WiseAgentMessage(message=ctx.get_current_query(), sender=self.name,
                                                       context_name=response.context_name), agent)
        return True

    def process_event(self, event):
        """Do nothing"""
        return True

    def process_error(self, error):
        """Log the error and return True."""
        logging.error(error)
        return True

    def stop(self):
        """Do nothing"""
        pass

    @property
    def name(self) -> str:
        """Get the name of the agent."""
        return self._name

    @property
    def response_delivery(self) -> Optional[Callable[[], WiseAgentMessage]]:
        """
        Get the function to deliver the response to the client.
        Returns:
            (Callable[[], WiseAgentMessage]): the function to deliver the response to the client
        """
        return self._response_delivery

    def set_response_delivery(self, response_delivery: Callable[[], WiseAgentMessage]):
        """
        Set the function to deliver the response to the client.
        Args:
            response_delivery (Callable[[], WiseAgentMessage]): the function to deliver the response to the
        """
        self._response_delivery = response_delivery

