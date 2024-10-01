import os

def assert_standard_variables_set():
    assert_env_vars_set(
        "GROQ_API_KEY",
        "NEO4J_USERNAME",
        "NEO4J_PASSWORD",
        "NEO4J_DATABASE",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "STOMP_USER",
        "STOMP_PASSWORD")

def assert_env_vars_set(*var_names: str):
    for var_name in var_names:
        assert_env_var_set(var_name)


def assert_env_var_set(var_name: str) -> str:
    value = os.getenv(var_name)
    assert value, f"Need to set the {var_name} environment variable"
    return value
