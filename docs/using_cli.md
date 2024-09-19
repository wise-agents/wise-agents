
# Wise Agents CLI Documentation

## Introduction

The Wise Agents CLI is a command-line interface for interacting with a multi-agent system built using the `wiseagents` framework. This tool allows you to:

- Load agents from YAML configuration files.
- Manage and reload agents dynamically.
- Send messages between agents.
- Trace message interactions.
- Start interactive chat sessions with agents.

This documentation will guide you through the installation, setup, and usage of the Wise Agents CLI.

## Distributed Wise Agents CLI

The Wise Agents CLI can be configured to start multiple instances of agents across different processes, network nodes, or even in separate pods (in Kubernetes environments). To enable this distributed architecture, you need to configure Redis for the `WiseAgentRegistry`. By setting up Redis, you allow the agents to share a common registry and message context, enabling asynchronous communication across distributed systems.

### Distributed Architecture

To learn more about how the CLI and agents can be scaled and managed in a distributed environment, please refer to the ["Distributed Architecture" paragraph in Wise Agents Architecture Document](wise_agents_architecture.md#distributed-architecture). This document outlines the key components, such as Redis integration, inter-agent communication, and load balancing strategies for deploying agents on different network nodes or cloud environments.


---

## Table of Contents

- [Installation and Setup](#installation-and-setup)
  - [Prerequisites](#prerequisites)
  - [Installing Dependencies](#installing-dependencies)
  - [Running the CLI](#running-the-cli)
- [Usage](#usage)
  - [Available Commands](#available-commands)
    - [`/help` or `/h`](#help-or-h)
    - [`/load-agents` or `/l`](#load-agents-or-l)
    - [`/reload-agents` or `/r`](#reload-agents-or-r)
    - [`/agents` or `/a`](#agents-or-a)
    - [`/send` or `/s`](#send-or-s)
    - [`/chat` or `/c`](#chat-or-c)
    - [`/trace` or `/t`](#trace-or-t)
    - [`/exit` or `/x`](#exit-or-x)
- [Agent Configuration](#agent-configuration)
  - [YAML Configuration File](#yaml-configuration-file)
- [Examples](#examples)
  - [Loading Agents](#loading-agents)
  - [Sending a Message to an Agent](#sending-a-message-to-an-agent)
  - [Starting a Chat Session](#starting-a-chat-session)
- [Notes](#notes)
- [Conclusion](#conclusion)

---

### Running the CLI

To start the Wise Agents CLI, run the script from your terminal:

```bash
python src/wiseagents/cli/wise_agent_cli.py [path_to_agents_file.yaml]
```

- The `[path_to_agents_file.yaml]` is optional. If provided, the CLI will automatically load agents from the specified YAML file upon startup.

---

## Usage

Once the CLI is running, you can interact with it using various commands. The CLI operates in a loop, prompting you for input after each command execution.

### Available Commands

#### `/help` or `/h`

Displays a list of available commands and their descriptions.

```plaintext
/(l)oad-agents: Load agents from file
/(r)eload agents: Reload agents from file
/(c)hat: Start a chat
/(t)race: Show the message trace
/e(x)it: Exit the application
/(h)elp: Show the available commands
(a)gents: Show the registered agents
(s)end: Send a message to an agent
```

#### `/load-agents` or `/l`

Loads agents from a YAML configuration file.

- **Usage**: Type `/load-agents` or `/l` and press ENTER.
- **File Path Prompt**: If no file path was provided when starting the CLI, you will be prompted to enter one.
  - Press ENTER without typing anything to use the default path: `src/wiseagents/cli/test-multiple.yaml`.
- **Agent Management**: Starts all loaded agents

#### `/reload-agents` or `/r`

Reloads agents from the current or a new YAML configuration file. This is very useful to reload agents when you are tweaking the configuration or the system prompt

- **Usage**: Type `/reload-agents` or `/r` and press ENTER.
- **File Path Prompt**: You can provide a new file path when prompted.
- **Agent Management**: Stops all currently running agents before reloading.

#### `/agents` or `/a`

Displays a list of all registered agents along with their descriptions.

#### `/send` or `/s`

Sends a message to a specific agent.

- **Usage**:
  1. Type `/send` or `/s` and press ENTER.
  2. Enter the agent's name when prompted.
  3. Enter the message you wish to send.

#### `/chat` or `/c`

Starts an interactive chat session with an agent.

- **Usage**:
  1. Type `/chat` or `/c` and press ENTER.
  2. Enter messages when prompted.
  3. Type `/back` to exit the chat session.

*Note: This command assumes that an agent named `PassThroughClientAgent1` is available and has been set up to handle chat interactions.*

#### `/trace` or `/t`

Displays the message trace, showing all messages that have been sent between agents.

#### `/exit` or `/x`

Exits the CLI and stops all running agents.

---

## Agent Configuration

### YAML Configuration File

Agents are defined in a YAML file, which the CLI loads to create and start agents. Each agent is specified with a YAML document starting with a tag that indicates the agent class.

**Example YAML Configuration:**

```yaml
--- !wiseagents.agents.PassThroughClientAgent
name: PassThroughClientAgent1
# Additional agent-specific configuration...
```

- The `!wiseagents.agents.PassThroughClientAgent` tag indicates the agent class.
- The `name` field specifies the unique name of the agent.
- Additional configuration parameters can be added as needed.

**Importing Agent Classes:**

When loading agents, the CLI attempts to import the necessary Python modules based on the tags in the YAML file. Ensure that:

- The agent classes are available in the Python path.
- The modules can be imported without errors.

---

## Examples

### Loading Agents

1. **Start the CLI** without specifying a file:

   ```bash
   python src/wiseagents/cli/wise_agent_cli.py
   ```

2. **At the prompt**, type:

   ```plaintext
   /load-agents
   ```

   or simply:

   ```plaintext
   /l
   ```

3. **Enter the file path** when prompted:

   ```plaintext
   Enter the file path (ENTER for default src/wiseagents/cli/test-multiple.yaml):
   ```

   - Press ENTER to use the default path.
   - Or enter a custom path to your YAML configuration file.

4. **Agents are loaded**:

   The CLI will import necessary modules and load agents, displaying messages like:

   ```plaintext
   Loaded agent: PassThroughClientAgent1
   registered agents= {'PassThroughClientAgent1': 'Description of agent'}
   ```

### Sending a Message to an Agent

1. **Ensure agents are loaded** and running.

2. **Type the send command**:

   ```plaintext
   /send
   ```

   or:

   ```plaintext
   /s
   ```

3. **Enter the agent's name** when prompted:

   ```plaintext
   Enter the agent name:
   ```

   - Example: `LLMOnlyWiseAgent2`

4. **Enter your message**:

   ```plaintext
   Enter the message:
   ```

   - Example: `Hello, how are you?`

5. **Message is sent**:

   The CLI will handle sending the message and waiting for a response.

### Starting a Chat Session

1. **Ensure `PassThroughClientAgent1`** is loaded and running.

2. **Type the chat command**:

   ```plaintext
   /chat
   ```

   or:

   ```plaintext
   /c
   ```

3. **Enter messages** when prompted:

   ```plaintext
   Enter a message (or /back):
   ```

   - Type your message and press ENTER.
   - Repeat to continue the conversation.

4. **Exit the chat**:

   - Type `/back` and press ENTER to return to the main command prompt.

---

## Notes

- **Agent Names**: Ensure that agent names used in commands match those defined in your YAML configuration file.
- **Module Importing**: The CLI attempts to import agent classes based on YAML tags. Modules must be importable and accessible in your Python environment.
- **Default File Path**: The default file path is set to `src/wiseagents/cli/test-multiple.yaml`. Modify this path as needed for your setup.

---

## Conclusion

The Wise Agents CLI provides a flexible and interactive way to manage and communicate with agents in a multi-agent system. By leveraging YAML configuration files and a straightforward command interface, you can simulate complex interactions, test agent behaviors, and monitor communications within the system.

For further customization, you can modify the agents and their configurations, extend the CLI with additional commands, or integrate it into larger applications.


