# wise-agents

# How to resolve dependencies declared in pyptoject.toml

1. Create a venv and activate it
``` 
python -m venv .venv
source .venv/bin/activate
```
2. ``pip install .``


# How to run test

1. Run ``pip install -e '.[test]'``
2. Start the llm service (see [model-serving/README.MD](model-serving/README.MD))
3. From project's root directory run ``pytest``
4. If you need log enable it running ``pytest --log-cli-level=DEBUG``
5. If you want to run a single test you can specify the test with -k option: ``pytest -k test_register_agents --log-cli-level=DEBUG``
6. You can also run all tests contained in a single file with the same option ``pytest -k test_WiseAgentRegistry --log-cli-level=DEBUG``
7. Note the name of the file could be partial so for example ``pytest -k test_yaml --log-cli-level=DEBUG`` will run test contained in ``tests/wiseagents/test_yaml_deserializer.py`` and ``tests/wiseagents/test_yaml_serialization.py)



# How to run the chatbot
1. Run ``pip install .``
2. Start the llm service (see [model-serving/README.MD](model-serving/README.MD))
2. Start artemis service (see [artemis/README.MD])(artemis/README.MD)
3. Set the ``STOMP_USER`` and ``STOMP_PASSWORD`` environment variables
4. Run the CLI ``python src/wiseagents/cli/wise_agent_cli.py``