import yaml
from wiseagents.yaml import WiseAgentsLoader

# This appears to be unused but actually does something!
import wiseagents.yaml


def test_yaml_env_var_not_set():
    loader = WiseAgentsLoader
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
    loader = WiseAgentsLoader
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
    loader = WiseAgentsLoader
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

    loader = WiseAgentsLoader
    test_values = yaml.load(input_with_defaults, loader)["test"]
    assert test_values["name"] == "Farah"
    assert test_values["url"] == "http://127.0.0.1:80/something"
    assert len(test_values["array"]) == 2
    assert test_values["array"][0] == "en"
    assert test_values["array"][1] == "to"


def test_data_types_sanity():
    # Sanity test to check the types of the values loaded from YAML

    loader = WiseAgentsLoader
    input = """
    test:
        int: 1
        number: 1.1
        trueLowerCase: true
        trueTitleCase: True
        trueUpperCase: TRUE
        falseLowerCase: false
        falseTitleCase: False
        falseUpperCase: FALSE
        string: hello world
        intString: "1"
        floatString: "1.1"
        array:
        - first
        - second
        dict:
            key: value  
    """

    test_values = yaml.load(input, loader)["test"]
    assert test_values["int"] == 1
    assert type(test_values["int"]) == int
    assert test_values["number"] == 1.1
    assert type(test_values["number"]) == float
    assert test_values["trueLowerCase"]
    assert type(test_values["trueLowerCase"]) == bool
    assert test_values["trueTitleCase"]
    assert type(test_values["trueTitleCase"]) == bool
    assert test_values["trueUpperCase"]
    assert type(test_values["trueUpperCase"]) == bool
    assert not test_values["falseLowerCase"]
    assert type(test_values["falseLowerCase"]) == bool
    assert not test_values["falseTitleCase"]
    assert type(test_values["falseTitleCase"]) == bool
    assert not test_values["falseUpperCase"]
    assert type(test_values["falseUpperCase"]) == bool
    assert test_values["string"] == "hello world"
    assert type(test_values["string"]) == str
    assert test_values["intString"] == "1"
    assert type(test_values["intString"]) == str
    assert test_values["floatString"] == "1.1"
    assert type(test_values["floatString"]) == str
    assert len(test_values["array"]) == 2
    assert type(test_values["array"]) == list
    assert test_values["array"][0] == "first"
    assert type(test_values["array"][0]) == str
    assert test_values["array"][1] == "second"
    assert type(test_values["array"][1]) == str
    assert type(test_values["dict"]) == dict
    assert test_values["dict"]["key"] == "value"
    assert type(test_values["dict"]["key"]) == str


def test_data_types_when_replaced_by_env_var(monkeypatch):
    loader = WiseAgentsLoader
    input = """
    test:
        int: ${INT}
        number: ${FLOAT}
        trueLowerCase: ${TRUE_LOWER_CASE}
        trueTitleCase: ${TRUE_TITLE_CASE}
        trueUpperCase: ${TRUE_UPPER_CASE}
        falseLowerCase: ${FALSE_LOWER_CASE}
        falseTitleCase: ${FALSE_TITLE_CASE}
        falseUpperCase: ${FALSE_UPPER_CASE}
        string: ${STRING}
        string_with_number_and_boolean: Hello ${INT} ${TRUE_TITLE_CASE}
        two_numbers: ${INT}${INT}
        two_numbers_float: ${INT}.${INT}
        intString: !env_var "${INT}"
        floatString: !env_var "${INT}.${INT}"

    """

    monkeypatch.setenv("INT", "1")
    monkeypatch.setenv("FLOAT", "1.1")
    monkeypatch.setenv("TRUE_LOWER_CASE", "true")
    monkeypatch.setenv("TRUE_TITLE_CASE", "True")
    monkeypatch.setenv("TRUE_UPPER_CASE", "TRUE")
    monkeypatch.setenv("FALSE_LOWER_CASE", "false")
    monkeypatch.setenv("FALSE_TITLE_CASE", "False")
    monkeypatch.setenv("FALSE_UPPER_CASE", "FALSE")
    monkeypatch.setenv("STRING", "hello world")

    test_values = yaml.load(input, loader)["test"]
    assert test_values["int"] == 1
    assert type(test_values["int"]) == int
    assert test_values["number"] == 1.1
    assert type(test_values["number"]) == float
    assert test_values["trueLowerCase"] == True
    assert type(test_values["trueLowerCase"]) == bool
    assert test_values["trueTitleCase"] == True
    assert type(test_values["trueTitleCase"]) == bool
    assert test_values["trueUpperCase"] == True
    assert type(test_values["trueUpperCase"]) == bool
    assert test_values["falseLowerCase"] == False
    assert type(test_values["falseLowerCase"]) == bool
    assert test_values["falseTitleCase"] == False
    assert type(test_values["falseTitleCase"]) == bool
    assert test_values["falseUpperCase"] == False
    assert type(test_values["falseUpperCase"]) == bool
    assert test_values["string"] == "hello world"
    assert type(test_values["string"]) == str
    assert test_values["string_with_number_and_boolean"] == "Hello 1 True"
    assert type(test_values["string_with_number_and_boolean"]) == str
    assert test_values["two_numbers"] == 11
    assert type(test_values["two_numbers"]) == int
    assert test_values["two_numbers_float"] == 1.1
    assert type(test_values["two_numbers_float"]) == float
    # TODO Should be 1 and 1.1 as strings - see https://github.com/wise-agents/wise-agents/issues/280
    assert test_values["intString"] == 1
    assert type(test_values["intString"]) == int
    assert test_values["floatString"] == 1.1
    assert type(test_values["floatString"]) == float



def test_data_types_when_replaced_by_env_var_default():
    loader = WiseAgentsLoader
    input = """
    test:
        int: ${INT:1}
        number: ${FLOAT:1.1}
        trueLowerCase: ${TRUE_LOWER_CASE:true}
        trueTitleCase: ${TRUE_TITLE_CASE:True}
        trueUpperCase: ${TRUE_UPPER_CASE:TRUE}
        falseLowerCase: ${FALSE_LOWER_CASE:false}
        falseTitleCase: ${FALSE_TITLE_CASE:False}
        falseUpperCase: ${FALSE_UPPER_CASE:FALSE}
        string: ${STRING:hello world}
        string_with_number_and_boolean: Hello ${INT:1} ${TRUE_TITLE_CASE:True}
        two_numbers: ${INT:1}${INT:1}
        two_numbers_float: ${INT:1}.${INT:2}
        intString: !env_var "${INT:1}"
        floatString: !env_var "${INT:1}.${INT:1}"

    """

    test_values = yaml.load(input, loader)["test"]
    assert test_values["int"] == 1
    assert type(test_values["int"]) == int
    assert test_values["number"] == 1.1
    assert type(test_values["number"]) == float
    assert test_values["trueLowerCase"] == True
    assert type(test_values["trueLowerCase"]) == bool
    assert test_values["trueTitleCase"] == True
    assert type(test_values["trueTitleCase"]) == bool
    assert test_values["trueUpperCase"] == True
    assert type(test_values["trueUpperCase"]) == bool
    assert test_values["falseLowerCase"] == False
    assert type(test_values["falseLowerCase"]) == bool
    assert test_values["falseTitleCase"] == False
    assert type(test_values["falseTitleCase"]) == bool
    assert test_values["falseUpperCase"] == False
    assert type(test_values["falseUpperCase"]) == bool
    assert test_values["string"] == "hello world"
    assert type(test_values["string"]) == str
    assert test_values["string_with_number_and_boolean"] == "Hello 1 True"
    assert type(test_values["string_with_number_and_boolean"]) == str
    assert test_values["two_numbers"] == 11
    assert type(test_values["two_numbers"]) == int
    assert test_values["two_numbers_float"] == 1.2
    assert type(test_values["two_numbers_float"]) == float
    # TODO Should be 1 and 1.1 as strings - see https://github.com/wise-agents/wise-agents/issues/280
    assert test_values["intString"] == 1
    assert type(test_values["intString"]) == int
    assert test_values["floatString"] == 1.1
    assert type(test_values["floatString"]) == float
