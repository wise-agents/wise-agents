# Wise Agents Coordination

One of the most important features of an AI multi-agent system is the ability for multiple
agents to work together to perform a complex task or solve a problem. The agents involved
in the system might make use of an LLM, but they don't have to, they could also perform
a task using an external API for example. The agents might also make use of different
LLM models.

Depending on the use case, agents may need to work together in different ways. Wise Agents
provides support for a couple different types of agent coordination: **sequential** and **phased**.
We'll take a closer look at each of these of coordination types in the next section.

Note that most LLM clients available today are designed to require the LLM provider to support
OpenAI tools in order to make use of tool calling. Notably, the agent coordination types provided
by Wise Agents make it possible to make use of tools and/or external APIs even when using an LLM
provider that doesn't support the use of the OpenAI tools. Moreover, the agent coordination types
provided by Wise Agents also make it possible to tackle more advanced use cases that require
more complex coordination between agents.

## What is sequential coordination?

We might need agents to collaborate in a sequential manner where we have a sequence of agents
and each agent in the sequence depends on the result from the previous agent in order to perform
its task. We'll refer to this type of coordination as **sequential** coordination. Here, an agent
performs a task and passes its result to the next agent in the sequence. The next agent processes
the received result and performs its own task, again passing its result on to the next agent in the
sequence until the final result from the last agent in the sequence is returned back to the client.

### How to make use of sequential coordination?

Wise Agents provides a `wiseagents.agents.SequentialCoordinatorWiseAgent` that you can use to
coordinate agents in a sequential manner. Once you've defined the agents you'd like to use
(using agents provided by Wise Agents and/or custom agents that you've created), you simply
need to specify the sequence of agents you'd like to use as a list of agent names when defining
your `SequentialCoordinatorWiseAgent`. For example, if you have two agents, named "Agent1" and
"Agent2", that you'd like to execute in a sequence, you'd specify `["Agent1", "Agent2"]`
for the `agents` parameter when creating your `SequentialCoordinatorWiseAgent`.

#### Want to see an example?

To see a complete example on how to make use of sequential coordination, check out the
`sequential_coordinator` [example](https://github.com/wise-agents/wise-agents/tree/main/examples/sequential_coordinator).

## What is phased coordination?

We might have a case where some agents are independent of each other and some agents depend on
each other. In this case, we can take advantage of the fact that some agents can be executed
together in parallel rather than executing all the agents in a sequence. Here, we make use of
what we are calling **phased coordination**, where agents are grouped into phases such that
agents in the same phase are independent of each other and thus can be run in parallel and
agents in a later phase depend on the results from agents in the previous phase. Here, each
agent will also add its results to the conversation history so that agents can take into
account results from previous agents when processing their own tasks.

### How to make use of phased coordination?

Wise Agents provides a `wiseagents.agents.PhasedCoordinatorWiseAgent` that you can use to
coordinate agents in a phased manner. You simply need to define the agents you'd like to use
(using agents provided by Wise Agents and/or custom agents that you've created) and also
define a `PhasedCoordinatorWiseAgent`.

#### How to define a `PhasedCoordinatorWiseAgent`?

When defining your `PhasedCoordinatorWiseAgent`, there are a few optional parameters that
you can specify: `phases`, `confidence_score_threshold`, and `max_iterations`.

* `phases`: This can be used to specify a list of phase names. The default value is 
`["Data Collection", "Data Analysis"]`. This list of phase names will be used by the
`PhasedCoordinatorWiseAgent` to determine the groups of agents that should be executed
for each phase. Use phase names that make sense for your use case.

* `confidence_score_threshold`: The confidence score threshold (between 0 and 100) to determine
if the final answer is acceptable. The default value is 85. If the final answer that's been
obtained after executing all the phases is less than the desired threshold, the
`PhasedCoordinatorWiseAgent` will attempt to rephrase the original query and try to execute
the phases again using the improved query to try to get to a better final answer.

* `max_iterations`: This can be used to specify the maximum number of iterations to run
the phases. The default value is 5. If the final answer that's been obtained after executing 
all the phases doesn't mean the desired threshold and the maximum number of iterations hasn't
been reached yet, then the `PhasedCoordinatorWiseAgent` will attempt to rephrase the original
query and try to execute the phases again.

#### How does a `PhasedCoordinatorWiseAgent` work?

A `PhasedCoordinatorWiseAgent` makes use of its LLM to determine the agents that should be
executed in parallel in phases. In particular, upon receiving a request, the LLM
will use the names and descriptions of the agents from the agents registry to determine the agents
that will be needed to solve the problem and will group the agents into phases taking into account
the phase names, where agents in a phase will be executed in parallel. The `PhasedCoordinatorWiseAgent`
will then kick off the first phase and once all the agents in that phase have finished performing their
tasks, the `PhasedCoordinatorWiseAgent` will move on to the next phase and so on until all phases
have been executed. 

Once all the phases have been executed, the `PhasedCoordinatorWiseAgent` will use its LLM to
determine the final answer to the original query along with a confidence score.

If the confidence score is equal to or exceeds the `confidence_score_threshold`, the final
answer will be returned to the client.

If the confidence score is less than the threshold, the `PhasedCoordinatorWiseAgent` will
use its LLM to attempt to rephrase the original query and try to execute the phases again using the
improved query to try to get to a better final answer. This process will be repeated until
the desired confidence score is achieved or until the max number of iterations has been reached.

> **_NOTE:_** The `PhasedCoordinatorWiseAgent` makes use of agent names and descriptions along
> with phase names to group the agents into phases. It's important to provide good descriptions
> for your agents to indicate their capabilities and dependencies. For example, if an agent
> depends on another agent, please indicate this in the agent's description.

#### Want to see an example?

TODO