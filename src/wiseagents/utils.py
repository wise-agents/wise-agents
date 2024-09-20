class AbstractClassError(Exception):
    pass


def enforce_no_abstract_class_instances(cls: type, check: type):
    """
    Check if a class has abstract methods.

    Args:
        cls (type): The class to check.
        check (type): cls should not be this

    :raises NotImplementedError: If the class has abstract methods.
    """
    for key, value in cls.__dict__.items():
        if cls is check:
            raise AbstractClassError(f"Class {cls.__name} is an abstract class and cannot be instantiated.")

