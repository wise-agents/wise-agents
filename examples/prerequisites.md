# Clone the Repository

If you haven't already, clone the Wise Agents repository from GitHub:

```bash
git clone https://github.com/wise-agents/wise-agents.git
cd wise-agents
```

# Configure and Start Redis

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

# Start artemis 

To support async communication between agents you need to have artemis up and running

1. Start artemis podman/docker image following instructions in [artemis README.MD](../../artemis/README.MD)

2. Set the environment variables for artemis secure login. If you haven't changed any configuration, starting artemis following the previous point instructions they are:

```bash
export STOMP_USER=artemis
export STOMP_PASSWORD=artemis
```

# Start Ollama with Llama 3.1

To support the Llama model, you need to ensure that Ollama is installed and running:

1. **Install Ollama** if it’s not installed already by following the [Ollama installation instructions](https://ollama.com).

2. **Start Ollama with Llama 3.1**:

   ```bash
   ollama run llama3.1
   ```

This will load the Llama 3.1 model into Ollama, which is necessary for running the intelligent agent.
