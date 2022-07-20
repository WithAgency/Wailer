from importlib import import_module


def import_class(path: str):
    """
    From a classe's reference, returns the class object (or really anything
    part of a module).

    Parameters
    ----------
    path
        Path to the class with the Python module, like foo.bar.SomeClass
    """

    module_name, class_name = path.rsplit(".", maxsplit=1)
    module = import_module(module_name)
    return getattr(module, class_name)
