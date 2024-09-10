import yaml
import re
import os

_env_pattern = re.compile(r".*?\${(.*?)}.*?")


def _env_constructor(loader, node):
    value = loader.construct_scalar(node)
    for group in _env_pattern.findall(value):
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
    return value


def setup():
    """
    Configures the YAML Loader to do replacement of environment variables.
    It will replace YAML value strings such as '${HOST}' and '${PORT:80}' with environment
    variable lookups.
    In the first example, '${HOST}', it will replace the string with the value from doing
    `os.getenv("HOST")`. If the environment variable 'HOST" is not set, an exception will be thrown.
    In the second example, '${PORT:80}', we are doing the same but looking up `os.getenv("PORT"). In this case,
    if the 'PORT' environment variable is not set, it will use the default value shows, which in this case is '80'.
    """
    yaml.add_implicit_resolver("!pathex", _env_pattern)
    yaml.add_constructor("!pathex", _env_constructor)

