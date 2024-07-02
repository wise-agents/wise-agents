# wise-agents

# How to resolve dependencies declared in pyptoject.toml

1. Create a venv and activate it
``` 
python -m venv .venv
source .venv/bin/activate
```
2. ``pip install .``


# How to run test

1. Run ``pip install .[test]``
2. Start the llm service (see [model-serving/README.MD](model-serving/README.MD))
3. From project's root directory run ``pytest``
4. If you need log enable it running ``pytest --log-cli-level=DEBUG``


```