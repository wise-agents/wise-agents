This directory contains examples of how to use the `wise-agents` multi-agent framework.

* [memory_agentic_chatbot](./memory_agentic_chatbot/README.md)
The example consists of two main agents:

    1. **Web Interface Agent**: Simulates a web-based client for interacting with other agents.
    2. **Intelligent Agent**: Handles requests and provides intelligent responses based on memory and context.
* [sequential_coordinator](./sequential_coordinator/README.md)
The example consists of four agents:

    1. **Web Interface Agent**: Simulates a web-based client for interacting with coordinator agent.
    2. **Literature Agent**: Handles requests and provides intelligent responses. Its system message says: 
    *"You are an english literature expert. Answer questions about english literature. Try to give context to your answers and provide quote from the books described. Your user is a native english speaker, with limited background in english literature."*
    3. **Translator Agent**: Handles requests and provides intelligent responses. Its system message says: 
    *"You are an expert translator from english to italian. Translate the provided text from english to italian. "*
    4. **SequentialCoordinator**: Take care of coordinating the request handling from the user delagating the work to other agents in a predetermined order.
* [run_examples_podman](./run_examples_podman/README.md)

    This guide walks you through running any of the example in the example directory in podman containers
