from importlib import import_module
from ipaddress import ip_address


def import_class(path: str):
    """
    From a class' reference, returns the class object (or really anything
    part of a module).

    Parameters
    ----------
    path
        Path to the class with the Python module, like foo.bar.SomeClass
    """

    module_name, class_name = path.rsplit(".", maxsplit=1)
    module = import_module(module_name)
    return getattr(module, class_name)


def is_loopback(host: str) -> bool:
    """
    Checks if a host name is a loopback address.

    This is used when guessing the domain name of the website through the
    "sites" framework.

    Notes
    -----
    This implementation is a bit wacky in sense that it's not guaranteed to be
    100% accurate, however this will work in most cases and getting really
    accurate would require making some DNS calls, which is not really
    a good idea since this is used in a default behavior.

    If this does not provide you satisfaction, feel free to use the
    `WAILER_BASE_URL` setting or to override
    {py:meth}`~.wailer.interfaces.BaseMessageType.get_base_url` in your email
    types.

    Parameters
    ----------
    host
        Domain/IP address that you want to check
    """

    if host == "localhost":
        return True
    else:
        try:
            return ip_address(host).is_loopback
        except ValueError:
            return False
