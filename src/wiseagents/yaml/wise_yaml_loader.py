import importlib
import yaml

from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser
from yaml.composer import Composer
from yaml.constructor import FullConstructor
from yaml.resolver import Resolver


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
            _WiseConstructor.__init__(self)
            Resolver.__init__(self)

            seen_classes = {}
            seen_packages = {}

            for token in yaml.scan(stream_copy):
                if type(token) is yaml.TagToken and token.value[0] == "!":
                    if token.value in seen_classes.keys():
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

class _WiseConstructor(FullConstructor):

    def construct_yaml_object(self, node, cls):
        super().construct_yaml_object(node, cls)

