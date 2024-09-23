import importlib
import os
import re
import yaml

from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser
from yaml.composer import Composer
from yaml.constructor import FullConstructor
from yaml.resolver import Resolver

_env_var_token = "env_var"
class WiseAgentsLoader(Reader, Scanner, Parser, Composer, FullConstructor, Resolver):

    def __init__(self, stream):
        opened_file = False
        try:
            stream_copy = None
            if isinstance(stream, str):
                stream_copy = "" + stream
            elif isinstance(stream, bytes):
                stream_copy = b"" + stream
            else:
                opened_file = True
                stream_copy = open(getattr(stream, 'name', "<file>"))

            Reader.__init__(self, stream)
            Scanner.__init__(self)
            Parser.__init__(self)
            Composer.__init__(self)
            FullConstructor.__init__(self)
            Resolver.__init__(self)

            seen_classes = {}
            seen_packages = {}

            for token in yaml.scan(stream_copy):
                if type(token) is yaml.TagToken and token.value[0] == "!":
                    if token.value in seen_classes.keys():
                        continue
                    if len(token.value) > 0 and token.value[1] == _env_var_token:
                        continue
                    seen_classes[token.value] = True
                    package_name = ""
                    for part in token.value[1].split(".")[:-1]:
                        package_name += part + "."
                    package_name = package_name[:-1]
                    if package_name in seen_packages.values():
                        continue
                    seen_packages[package_name] = True
                    importlib.import_module(package_name)

        finally:
            if opened_file:
                stream_copy.close()

    def construct_document(self, node):
        return super().construct_document(node)

_env_pattern = re.compile(r".*?\${(.*?)}.*?")


def _env_constructor(loader, node):
    value = loader.construct_scalar(node)
    groups = _env_pattern.findall(value)

    for group in groups:
        env_var = group
        default = None
        if ":" in group:
            parts = group.split(":")
            if len(parts) != 2:
                raise Exception(f"Invalid value '{group}' in '{value}'")
            env_var = parts[0]
            default = parts[1]

        env_value = os.getenv(env_var)
        if env_value == None and default != None:
            env_value = default

        if env_value == None:
            raise Exception(f"No environment variable called '{env_var}', and no default value was specified for '{value}'")

        value = value.replace(f"${{{group}}}", env_value)

    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False

    try:
        return int(value)
    except:
        pass

    try:
        return float(value)
    except:
        pass

    return value

def setup_yaml_for_env_vars():
    """
    Configures the YAML Loader to do replacement of environment variables.
    It will replace YAML value strings such as '${HOST}' and '${PORT:80}' with environment
    variable lookups.
    In the first example, '${HOST}', it will replace the string with the value from doing
    `os.getenv("HOST")`. If the environment variable 'HOST" is not set, an exception will be thrown.
    In the second example, '${PORT:80}', we are doing the same but looking up `os.getenv("PORT"). In this case,
    if the 'PORT' environment variable is not set, it will use the default value shows, which in this case is '80'.
    """
    yaml.add_implicit_resolver(f"!{_env_var_token}", _env_pattern)
    yaml.add_constructor(f"!{_env_var_token}", _env_constructor)

    yaml.add_implicit_resolver(f"!{_env_var_token}", _env_pattern, Loader=WiseAgentsLoader)
    yaml.add_constructor(f"!{_env_var_token}", _env_constructor, Loader=WiseAgentsLoader)