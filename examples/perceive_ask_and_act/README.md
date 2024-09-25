
# Perceive, ask and Act Example

This guide walks you through running a practical example of a multi-agent system using Wise Agents. In this example, six agents (an agent interacting with a human with a text based interface, a sequential agent coordinator, and four intelligent agents) are started, allowing you to experiment with agents/humans communication and interaction in a simulated environment. It uses a sequential coordination able to share chat history between involved agents.


## Example Overview

The example consists of six agents:

1. **PerceivingAgent**: This is an agent that can perceive file changes. In case of changes it send a message with the list of books contained in books_read.txt to the SequentialCoordinator. This agent code is not part of wise-agents framework, but it's defined for this example use only in `custom_agent.py` present in the example directory.
2. **LiterateAgent**: Handles requests and provides intelligent responses. Its system message says: 
*"You are an english literature expert. The user will provide you with a list of books they have read. Suggest the next 5 books they should read and ask user for their favorite one in this list"*
3. **UserQuestionAgent**: ask a question to the user and pass over the answer as part of the flow. This is not defined in the yaml, but started from `custom_agent.py` instantiating the agent from the code. It provides also a very simple text based interface to ask a question which is needed to complete the designed flow. 
4. **FinalLiterateAgent**: Handles requests and provides intelligent responses. Its system message says: 
*"You will receive a preference from the user. Considering the previous books read , the user's preference on your first list of suggestion, suggest the next 3 books they should read."*
5. **ActionAgent**: This agent will write what received (the books suggested) in a file (books_suggested.txt). It will override the file each time. This agent code is not part of wise-agents framework, but it's defined for this example use only in `custom_agent.py` present in the example directory.
6. **SequentialCoordinator**: Take care of coordinating the request handling from the user delagating the work to other agents in a predetermined order. Note the SequentialCoordinar here will use the `wiseagents.agents.SequentialMemoryCoordinatorWiseAgent` which share the chat history between all agents involved in the sequence, permitting them to make reasoning based on all the interaction with LLM happened in previous step. In this example, the **FinalLiterateAgent** will use info coming from **PerceivingAgent**, **LiterateAgent**, and **UserQuestionAgent** to produce the final list of 3 suggested books.

These agents are defined in YAML configuration files located in the `examples/perceive_ask_and_act` directory.

## Prerequisite For Running the Example
1. Clone the repository
2. Configure and start redis
3. Start artemis
4. Start Ollama

For detailed instructions on how to satisfy those prerequisite please refer to [prerequisites.md](../prerequisites.md)


### Step 1: Start the Intelligent Agent

In a console, run the intelligent agents and coordinator agent. Having custom created agents in the directory of example you need to run the script from there after setting PYTHONPATH env variable. Here you have all the commands needed pretending you are in the project main directory:

```bash
cd examples/perceive_ask_and_act
export PYTHONPATH="."
python ../../src/wiseagents/cli/wise_agent_cli.py ./intelligent-agents.yaml
```

This will initialize the intelligent agents and coordinator agent, which will be ready to watch `books_read.txt` for changes.

### Step 2: Start UserQuestionAgent
In a console, start the UserQuestionAgent. Having custom created agents in the directory of example you need to run the script from there after setting PYTHONPATH env variable. Here you have all the commands needed pretending you are in the project main directory:

```bash
cd examples/perceive_ask_and_act
export PYTHONPATH="."
python ./custom_agents.py
```

This will initialize the UserQuestionAgent, and  will be ready to show question and accept answer from the user.

### Step 3: Interaction

Once all agents are up and running, you can edit `books_read.txt` file and `PerceivingAgent` will start sending requests to the coordinator agent. The coordinator agent will take care to interact to the `LiterateAgent`. `Literate Agent` will create a list of 5 suggested books and a question asking the user for a preference. Then the message will be sent to `UserQuestionAgent` which will show the list and the question in the console, asking for an answer. The answer inserted by the user will be passed  to the `ActionAgent` which will write the results to `books_suggested.txt`. You will be able to see the interaction between the agents through the logs in both consoles.


### Step 4: Experiment

You can experiment with different agent configurations or modify the agent behaviors by editing the YAML files located in the `examples/perceive_ask_and_act` directory. These configuration files define the agents' properties, including memory, communication methods, and response patterns. You can do that without restarting everything, just edit the yaml file(s) and use CLI's /reload command (see our documentation for more details on how to use CLI)

## Understanding the YAML Configuration and custom_agents.py

- **intelligent-agents.yaml**: Defines all the agents discussed in this document and needed to run the example
- **custom_agents.py**: contain 3 custom agents defined for the purpose of this example. It has also a `main()` function which instantiate the `UserQuestionAgent` 

These YAML files include the specific `WiseAgent` classes and configuration needed to run the agents. Feel free to explore and modify these files to customize the agents' behavior.

## Additional Resources

For more information about the architecture and advanced configurations of wise-agents, refer to the [Wise Agents Architecture Document](wise_agents_architecture.md), which provides insights into how the system can be scaled and deployed in distributed environments.

## Conclusion

By following these steps, you have successfully run a simple sequential coordinated multi-agent chatbot using Wise Agents. You can now explore further by modifying agent behaviors, adding new agents, or experimenting with different message flows.

For any further assistance, feel free to refer to the official Wise Agents documentation or reach out to the repository maintainers.