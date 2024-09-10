import yaml

# This appears to be unused but actually does something!
import wiseagents.yaml_env

wiseagents.yaml_env.setup()


def test_yaml_env_var_not_set():
    loader = yaml.FullLoader
    input = """
    test:
        name: ${NAME}
    """
    error = False
    try:
        test_values = yaml.load(input, loader)
    except (Exception):
        error = True

    assert error, "An error should have happened since the NAME variable is not set"


def test_yaml_env_var_set(monkeypatch):
    input = """
    test:
        name: ${NAME}
        url: http://${HOST}:${PORT}/something
        array:
        - ${ONE}
        - ${TWO}
    """
    loader = yaml.FullLoader
    monkeypatch.setenv("NAME", "Stefano")
    monkeypatch.setenv("HOST", "192.168.0.1")
    monkeypatch.setenv("PORT", "433")
    monkeypatch.setenv("ONE", "ein")
    monkeypatch.setenv("TWO", "zwei")
    test_values = yaml.load(input_with_defaults, loader)["test"]
    assert test_values["name"] == "Stefano"
    assert test_values["url"] == "http://192.168.0.1:433/something"
    assert len(test_values["array"]) == 2
    assert test_values["array"][0] == "ein"
    assert test_values["array"][1] == "zwei"



input_with_defaults = """
test:
    name: ${NAME:Kabir}
    url: http://${HOST:localhost}:${PORT:8080}/something
    array:
    - ${ONE:uno}
    - ${TWO:dos}
"""

def test_yaml_with_defaults_no_env_vars_set():
    loader = yaml.FullLoader
    test_values = yaml.load(input_with_defaults, loader)["test"]
    assert test_values["name"] == "Kabir"
    assert test_values["url"] == "http://localhost:8080/something"
    assert len(test_values["array"]) == 2
    assert test_values["array"][0] == "uno"
    assert test_values["array"][1] == "dos"

def test_yaml_with_defaults_env_vars_set(monkeypatch):
    monkeypatch.setenv("NAME", "Farah")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "80")
    monkeypatch.setenv("ONE", "en")
    monkeypatch.setenv("TWO", "to")

    loader = yaml.FullLoader
    test_values = yaml.load(input_with_defaults, loader)["test"]
    assert test_values["name"] == "Farah"
    assert test_values["url"] == "http://127.0.0.1:80/something"
    assert len(test_values["array"]) == 2
    assert test_values["array"][0] == "en"
    assert test_values["array"][1] == "to"
