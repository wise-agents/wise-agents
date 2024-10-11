
# Sequential Coordinator Example: Answer and Translate Chatbot

This guide walks you through running a practical example of a multi-agent system using Wise Agents. In this example, four agents (a web interface agent, a sequential agent coordinator, and two intelligent agents) are started, allowing you to experiment with agent communication and interaction in a simulated environment, with a sequential coordination.


## Example Overview

The example consists of four agents:

1. **Web Interface Agent**: Simulates a web-based client for interacting with coordinator agent.
2. **Literature Agent**: Handles requests and provides intelligent responses. Its system message says: 
*"You are an english literature expert. Answer questions about english literature. Try to give context to your answers and provide quote from the books described. Your user is a native english speaker, with limited background in english literature."*
3. **Translator Agent**: Handles requests and provides intelligent responses. Its system message says: 
*"You are an expert translator from english to italian. Translate the provided text from english to italian. "*
4* **SequentialCoordinator**: Take care of coordinating the request handling from the user delagating the work to other agents in a predetermined order.

These agents are defined in YAML configuration files located in the `examples/sequential_coordinator` directory.

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

### Step 4: Start Ollama with Llama 3.2

To support the Llama model, you need to ensure that Ollama is installed and running:

1. **Install Ollama** if it’s not installed already by following the [Ollama installation instructions](https://ollama.com).

2. **Start Ollama with Llama 3.2**:

   ```bash
   ollama run llama3.2:1b
   ```

This will load the Llama 3.2 model into Ollama, which is necessary for running the intelligent agent.

### Step 5: Start the Intelligent Agent

In a first console, run the intelligent agents and coordinator agent, also from the project’s home directory, using the following command:

```bash
python src/wiseagents/cli/wise_agent_cli.py examples/sequential_coordinator/intelligent-agents.yaml
```

This will initialize the intelligent agents and coordinator agent, which will be ready to respond to requests sent by the web interface agent.


### Step 6: Start the Web Interface Agent

In your second console, navigate to the project’s home directory and run the web interface agent using the provided YAML configuration file:

```bash
python src/wiseagents/cli/wise_agent_cli.py examples/sequential_coordinator/web-interface.yaml
```

This will initialize the Assistant agent with its web interface. You should see logs indicating that the agent is started and waiting for requests. You will see in the console also a web server listening at [http://127.0.0.1:7860](http://127.0.0.1:7860)

```plain-text
Running on local URL:  http://127.0.0.1:7860
```

### Step 7: Interaction

Once all agents are up and running, you can use the web interface agent as a chatbot and it will start sending requests to the intelligent agent. You will be able to see the interaction between the agents through the logs in both consoles.
Try as an example to ask something like "Can you give me detailed information about Harry Potter". You will get the detailed information about Rowling's books translated in Italian :)

### Step 8: Experiment

You can experiment with different agent configurations or modify the agent behaviors by editing the YAML files located in the `examples/sequential_coordinator` directory. These configuration files define the agents' properties, including memory, communication methods, and response patterns. You can do that without restarting everything, just edit the yaml file(s) and use CLI's /reload command (see our documentation for more details on how to use CLI)

## Understanding the YAML Configuration

- **web-interface.yaml**: Defines the web interface agent, which serves as the client interface for interacting with other agents.
- **intelligent-agents.yaml**: Defines the intelligent agents and coordinator agent, which processes the requests and generates responses based on the provided input.

These YAML files include the specific `WiseAgent` classes and configuration needed to run the agents. Feel free to explore and modify these files to customize the agents' behavior.

## Additional Resources

For more information about the architecture and advanced configurations of wise-agents, refer to the [Wise Agents Architecture Document](wise_agents_architecture.md), which provides insights into how the system can be scaled and deployed in distributed environments.

## Conclusion

By following these steps, you have successfully run a simple sequential coordinated multi-agent chatbot using Wise Agents. You can now explore further by modifying agent behaviors, adding new agents, or experimenting with different message flows.

For any further assistance, feel free to refer to the official Wise Agents documentation or reach out to the repository maintainers.