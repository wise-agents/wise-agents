import abc
import yaml

from wiseagents import enforce_no_abstract_class_instances


class WiseAgentsYAMLObject(yaml.YAMLObject):
    """
        Abstract class to deal with removing the underscores from the keys of the parsed YAML object.
    """

    def __init__(self):
        enforce_no_abstract_class_instances(self.__class__, WiseAgentsYAMLObject)

    def __setstate__(self, d):
        """
        Sets the state of the object from the parsed representation of the YAML or from Pickle.
        This does conversion of the keys read, which have no leading underscores to the internal representation
        in the class which have leading underscores.

        Note: Subclasses MAY override this method, but need to be aware that the keys in the dictionary will not have
        underscores, and once done they will need to call this method via a super().__setstate__(d) call.

        Note: Rather than overriding __setstate__(), it is preferred to override _validate_and_convert_types(), which
        will be called once conversion has been done, and have the keys in the dictionary with underscores.

        Args:
            d (dict): the parsed representation of the YAML object

        Returns:
            the modified state dictionary of the object we are deserializing
        """
        d = self._convert_yaml_keys_to_members(d)

        self._validate_and_convert_types(d)

        for key, value in d.items():
            setattr(self, key, value)

    def __getstate__(self) -> dict:
        """
        Gets the state of the object for serialization to YAML/Pickle.
        This converts the keys from their internal representation with leading underscores to the external
        representation, which have no leading underscores.

        Note: subclasses overriding this method should call super().__getstate__() to get the state that will
        be serialized to YAML/Pickle, rather than calling self.__dict__ directly.

        Note: when overriding this method and getting the state, e.g. for deleting entries which should not be
        serialized, the entries in the map will have keys in the external form (i.e. no leading underscores).

        Returns:
            the modified state dictionary of the object we are serializing
        """
        d: dict = self.__dict__.copy()
        if d:
            d = self._convert_members_to_yaml_keys(d)
        return d

    @classmethod
    def _convert_yaml_keys_to_members(cls, d: dict) -> dict:
        """
        Translate the dictionary by adding underscores to all the keys.
        The resulting dictionary is used to set the state of the object.

        Args:
            d (dict): the parsed representation of the YAML object

        Returns:
            the modified state dictionary of the object we are deserializing, or the original dictionary if not changes are needed
        """

        copy = {}
        for key, value in d.items():
            # if not key.startswith('_'):
            key = f"_{key}"
            copy[key] = value
        return copy


    @abc.abstractmethod
    def _validate_and_convert_types(self, d: dict) -> dict:
        """
        Validate the dictionary and convert the types of the values.
        Subclasses may override this method to provide custom validation and type conversion.

        Args:
            d (dict): the parsed representation of the YAML object
        """
        return d

    @classmethod
    def _convert_members_to_yaml_keys(cls, d: dict) -> dict:
        """
        Translate the dictionary by removing underscores from all the keys

        Args:
            d (dict): the state dictionary of the object we are serializing
        """

        copy = {}
        for key, value in d.items():
            if key.startswith('_'):
                key = key[1:]
                copy[key] = value
        return copy
