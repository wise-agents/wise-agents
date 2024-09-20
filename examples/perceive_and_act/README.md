
# Perceive and Act Example

This guide walks you through running a practical example of a multi-agent system using Wise Agents. In this example, four agents (a web interface agent, a sequential agent coordinator, and two intelligent agents) are started, allowing you to experiment with agent communication and interaction in a simulated environment, with a sequential coordination.


## Example Overview

The example consists of four agents:

1. **PerceivingAgent**: This is an agent that can perceive file changes. In case of changes it send a message with the list of books contained in books_read.txt to the SequentialCoordinator. This agent code is not part of wise-agents framework, but it's defined for this example use only in `custom_agent.py` present in the example directory.
2. **Literate Agent**: Handles requests and provides intelligent responses. Its system message says: 
*"You are an english literature expert. The user will provide you with a list of books they have read. Suggest the next 3 books they should read."*
3. **ActionAgent**: This agent will write what received (the books suggested) in a file (books_suggested.txt). It will override the file each time. This agent code is not part of wise-agents framework, but it's defined for this example use only in `custom_agent.py` present in the example directory.
4. **SequentialCoordinator**: Take care of coordinating the request handling from the user delagating the work to other agents in a predetermined order.

These agents are defined in YAML configuration files located in the `examples/perceive_and_act` directory.

## Prerequisite For Running the Example
1. Clone the repository
2. Configure and start redis
3. Start artemis
4. Start Ollama

For detailed instructions on how to satisfy those prerequisite please refer to [prerequisites.md](../prerequisites.md)


### Step 1: Start the Intelligent Agent

In a console, run the intelligent agents and coordinator agent. Having custom creted agents in the directory of example you need to run the script from there after setting PYTHONPATH env variable. Here you have all the commands needed pretending you are in the project main directory:

```bash
cd examples/perceive_and_act
export PYTHONPATH="."
python ../../src/wiseagents/cli/wise_agent_cli.py ./intelligent-agents.yaml
```

This will initialize the intelligent agents and coordinator agent, which will be ready to watch `books_read.txt` for changes.


### Step 2: Interaction

Once all agents are up and running, you can edit `books_read.txt` file and `PerceivingAgent` will start sending requests to the coordinator agent. The coordinator agent will take care to interact to the `LiterateAgent` passing its response to the `ActionAgent` which will write the results to `books_suggested.txt. You will be able to see the interaction between the agents through the logs in both consoles.


### Step 3: Experiment

You can experiment with different agent configurations or modify the agent behaviors by editing the YAML files located in the `examples/perceive_and_act` directory. These configuration files define the agents' properties, including memory, communication methods, and response patterns. You can do that without restarting everything, just edit the yaml file(s) and use CLI's /reload command (see our documentation for more details on how to use CLI)

## Understanding the YAML Configuration

- **intelligent-agents.yaml**: Defines all the agents discussed in this document and needed to run the example

These YAML files include the specific `WiseAgent` classes and configuration needed to run the agents. Feel free to explore and modify these files to customize the agents' behavior.

## Additional Resources

For more information about the architecture and advanced configurations of wise-agents, refer to the [Wise Agents Architecture Document](wise_agents_architecture.md), which provides insights into how the system can be scaled and deployed in distributed environments.

## Conclusion

By following these steps, you have successfully run a simple sequential coordinated multi-agent chatbot using Wise Agents. You can now explore further by modifying agent behaviors, adding new agents, or experimenting with different message flows.

For any further assistance, feel free to refer to the official Wise Agents documentation or reach out to the repository maintainers.