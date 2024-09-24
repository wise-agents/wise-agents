# How To Create Custom Agents

Wise Agents provides some agent implementations out of the box in the `wiseagents.agents` package,
but you can also create your own agents.

To create a custom agent, you need to extend the `wiseagents.core.WiseAgent` class and implement 
the following abstract methods from this class: `process_request`, `process_response`, `process_error`,
and `process_event`. Let's take a closer look at these methods.

## Implementing the `process_request` method

**Method signature:**
```
def process_request(self, request: WiseAgentMessage,
                    conversation_history: List[ChatCompletionMessageParam]) -> Optional[str]:
```

This method is used by the agent to process the given `request` message. It is invoked by
`WiseAgent.handle_request`. This method should return the agent's response to the given request
as a `str` or `None` if there is no response needed.

When processing the request, the agent can make use of the given `conversation_history`,
which is a `List` of `ChatCompletionMessageParam` objects. If there is a chat session associated
with the request, this list will contain the message history. In particular, if the agent has
been invoked by a `PhasedCoordinatorWiseAgent` or an `AssistantAgent`, there will be a chat session
associated with the request. The agent can make use of this conversation history when calling its
`WiseAgentLLM`'s `process_chat_completion` method. If there isn't a chat session associated with
the request, the `conversation_history` list will be empty.

The response returned by the `process_request` method will be used by `WiseAgent.handle_request`
to create and send a message to the appropriate agent. This destination agent will depend on the
type of collaboration that the agent is involved in. For example, if the agent has been invoked
by a `PhasedCoordinatorWiseAgent` or an `AssistantAgent`, the response message will be sent back
to that agent and the conversation history will be updated with the response as well. If the agent
is involved in sequential coordination, the response will be sent to either the next agent in the
sequence or back to the original requester if there are no more agents remaining.

For more details about sequential and phased coordination, see the
[Wise Agents Coordination](./agent_coordination.md) section.

## Implementing the `process_response` method

**Method signature:**
```
def process_response(self, message: WiseAgentMessage) -> bool:
```

This method is used by the agent to process a response `message` that it has received from another agent,
i.e., this method is invoked after this agent has sent a request to another agent and receives a response
message back from the other agent. This method should return `True` if the given message was processed
successfully and `False` otherwise.

## Implementing the `process_error` method

**Method signature:**
```
def process_error(self, error: Exception) -> bool:
```

This method is used by the agent to process an error. This method should return `True` if the given
error was process successfully and `False` otherwise.

## Implementing the `process_event` method

**Method signature:**
```
def process_event(self, event: WiseAgentEvent) -> bool:
```

This method will be used by an agent to process an event. The `WiseAgentEvent` class is still under
construction (keep an eye on https://github.com/wise-agents/wise-agents/issues/8 for future updates).
For now, this method can be implemented by simply using a `pass` statement as the method body.
