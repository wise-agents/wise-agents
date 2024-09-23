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

* [peceive_and_act](./perceive_and_act/README.md) 
The example consists of four agents:

    1. **PerceivingAgent**: This is an agent that can perceive file changes. In case of changes it send a message with the list of books contained in books_read.txt to the SequentialCoordinator. This agent code is not part of wise-agents framework, but it's defined for this example use only in `custom_agent.py` present in the example directory.
    2. **Literate Agent**: Handles requests and provides intelligent responses. Its system message says: 
    *"You are an english literature expert. The user will provide you with a list of books they have read. Suggest the next 3 books they should read."*
    3. **ActionAgent**: This agent will write what received (the books suggested) in a file (books_suggested.txt). It will override the file each time. This agent code is not part of wise-agents framework, but it's defined for this example use only in `custom_agent.py` present in the example directory.
    4. **SequentialCoordinator**: Take care of coordinating the request handling from the user delagating the work to other agents in a predetermined order.



* [run_examples_podman](./run_examples_podman/README.md)

    This guide walks you through running any of the example in the examples directory in podman containers
