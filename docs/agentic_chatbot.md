
# Wise Agents Example: Memory Agentic Chatbot

This guide walks you through running a practical example of a multi-agent system using Wise Agents. In this example, two agents (a web interface agent and an intelligent agent) are started, allowing you to experiment with agent communication and interaction in a simulated environment.


## Example Overview

The example consists of two main agents:

1. **Web Interface Agent**: Simulates a web-based client for interacting with other agents.
2. **Intelligent Agent**: Handles requests and provides intelligent responses based on memory and context.

These agents are defined in YAML configuration files located in the `examples/memory_agentic_chatbot` directory.

## Running the Example

### Step 1: Clone the Repository

If you haven't already, clone the Wise Agents repository from GitHub:

```bash
git clone https://github.com/wise-agents/wise-agents.git
cd wise-agents
```

### Step 2: Configure and Start Redis

In this step, we will set up Redis for agent context and registry.

1. **Create a hidden directory `.wise-agents`** in the root of your project:

   ```bash
   mkdir .wise-agents
   ```

2. **Copy the Redis configuration file** as shown in the [`.wise-agents` directory](https://github.com/wise-agents/wise-agents/tree/main/.wise-agents) from the GitHub repo. Create a file named `redis-config.yaml` inside `.wise-agents`:

   ```yaml
   redis:
     host: localhost
     port: 6379
   ```

3. **Ensure Redis is installed and running**. You can start redis as podman/docker image following instruction in [redis README.MD](../../redis/README.MD)

### Step 3: Start artemis 

To support async communication between agents you need to have artemis up and running

1. Start artemis podman/docker image following instructions in [artemis README.MD](../../artemis/README.MD)

2. Set the environment variables for artemis secure login. If you haven't changed any configuration, starting artemis following the previous point instructions they are:

```bash
export STOMP_USER=artemis
export STOMP_PASSWORD=artemis
```

### Step 4: Start Ollama with Llama 3.1

To support the Llama model, you need to ensure that Ollama is installed and running:

1. **Install Ollama** if it’s not installed already by following the [Ollama installation instructions](https://ollama.com).

2. **Start Ollama with Llama 3.1**:

   ```bash
   ollama run llama3.1
   ```

This will load the Llama 3.1 model into Ollama, which is necessary for running the intelligent agent.

### Step 5: Start the Intelligent Agent

In a second console, run the intelligent agent, also from the project’s home directory, using the following command:

```bash
python src/wiseagents/cli/wise_agent_cli.py examples/memory_agentic_chatbot/intelligent-agent.yaml
```

This will initialize the intelligent agent, which will be ready to respond to requests sent by the web interface agent.


### Step 6: Start the Web Interface Agent

In your first console, navigate to the project’s home directory and run the web interface agent using the provided YAML configuration file:

```bash
python src/wiseagents/cli/wise_agent_cli.py examples/memory_agentic_chatbot/web-interface.yaml
```

This will initialize the Assitant agent with its web interface. You should see logs indicating that the agent is started and waiting for requests. You will see in the console also a web server listening at [http://127.0.0.1:7860](http://127.0.0.1:7860)

```plain-text
Running on local URL:  http://127.0.0.1:7860
```

### Step 7: Interaction

Once both agents are up and running, you can use the web interface agent as a chatbot and it will start sending requests to the intelligent agent. You will be able to see the interaction between the two agents through the logs in both consoles.

### Step 8: Experiment

You can experiment with different agent configurations or modify the agent behaviors by editing the YAML files located in the `examples/memory_agentic_chatbot` directory. These configuration files define the agents' properties, including memory, communication methods, and response patterns.

## Understanding the YAML Configuration

- **web-interface.yaml**: Defines the web interface agent, which serves as the client interface for interacting with other agents.
- **intelligent-agent.yaml**: Defines the intelligent agent, which processes the requests and generates responses based on the provided input.

These YAML files include the specific `WiseAgent` classes and configuration needed to run the agents. Feel free to explore and modify these files to customize the agents' behavior.

## Additional Resources

For more information about the architecture and advanced configurations of wise-agents, refer to the [Wise Agents Architecture Document](wise_agents_architecture.md), which provides insights into how the system can be scaled and deployed in distributed environments.

## Conclusion

By following these steps, you have successfully run a simple memory-agentic chatbot using Wise Agents. You can now explore further by modifying agent behaviors, adding new agents, or experimenting with different message flows.

For any further assistance, feel free to refer to the official Wise Agents documentation or reach out to the repository maintainers.
