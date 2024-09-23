
# How to run examples in podman container

This guide walks you through running any of the example in the example directory in podman containers


These agents are defined in YAML configuration files located in the `examples/sequential_coordinator` directory.

## Running the Examples

### Step 1: Clone the Repository

If you haven't already, clone the Wise Agents repository from GitHub:

```bash
git clone https://github.com/wise-agents/wise-agents.git
cd wise-agents
```

### Step 2: Install podman 

If you have not yet installed podman please follow the [official installation instructions](https://podman.io/docs/installation)

### Step 3: Build wise-agent container

From the project root directory (where you cloned it in [step 1](#step-1-clone-the-repository)):

```bash
podman build -t wise-agents -f examples/run_examples_podman/container-wise-agents --env STOMP_USER,STOMP_PASSWORD .
```

This will build a container with all everything needed to run cli and so any of the other example. Note we are passing environment variables needed to run the examples (you can use also wildcards like```STOMP*```). If any of the example has any other.
Note also that any configuartion is static in the container by definition. So, as an example, registry's configuartion of the container will be the one in ```$PROJECT_HOME/.wise-agents/registry.yaml``` 


### Step 4: Start the agents
Now you can start agents invoking CLI using the generated image. Here as an example you have the steps to run [memory_agentic_chatbot](../memory_agentic_chatbot/README.md) in containers

1. Complete all prerequisites until step 5 as described in the example's [README.md](../memory_agentic_chatbot/README.md)

2. Start the Intelligent Agent

    In a first console, navigate to the project’s home directory and run the intelligent agent in the generate container: 

    ```bash
    podman run -it --network=pasta:-t,auto,-u,auto,-T,auto,-U,auto wise-agents:latest python src/wiseagents/cli/wise_agent_cli.py examples/memory_agentic_chatbot/intelligent-agent.yaml
    ```

    This will initialize the intelligent agent, which will be ready to respond to requests sent by the web interface agent.


3. Start the Web Interface Agent

In a second console, navigate to the project’s home directory and run the web interface in the generated contained:

```bash
podman run -it --network=pasta:-t,auto,-u,auto,-T,auto,-U,auto wise-agents:latest python src/wiseagents/cli/wise_agent_cli.py  python src/wiseagents/cli/wise_agent_cli.py examples/memory_agentic_chatbot/web-interface.yaml
```


### Step 5: Experiment

You can experiment with different [examples](../README.md) following the instructions of the specific example for the yaml configuartion and use.

## Additional Resources

For more information about the architecture and advanced configurations of wise-agents, refer to the [Wise Agents Architecture Document](wise_agents_architecture.md), which provides insights into how the system can be scaled and deployed in distributed environments.

## Conclusion

By following these steps, you have successfully run a simple sequential coordinated multi-agent chatbot using Wise Agents. You can now explore further by modifying agent behaviors, adding new agents, or experimenting with different message flows.

For any further assistance, feel free to refer to the official Wise Agents documentation or reach out to the repository maintainers.