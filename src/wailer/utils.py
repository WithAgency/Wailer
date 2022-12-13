from importlib import import_module
from ipaddress import ip_address
from urllib.parse import urljoin, urlparse

from lxml import etree
from premailer import Premailer


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


class MjmlPremailer(Premailer):
    def transform(self, html=None, pretty_print=True, **kwargs):
        """
        Stripped-down version of the original transform method that does only
        deal with links and image URLs.
        """

        if html is not None and self.html is not None:
            raise TypeError("Can't pass html argument twice")
        elif html is None and self.html is None:
            raise TypeError("must pass html as first argument")
        elif html is None:
            html = self.html
        if hasattr(html, "getroottree"):
            root = html.getroottree()
            page = root
        else:
            if self.method == "xml":
                parser = etree.XMLParser(ns_clean=False, resolve_entities=False)
            else:
                parser = etree.HTMLParser()
            stripped = html.strip()

            tree = etree.fromstring(stripped, parser).getroottree()
            page = tree.getroot()
            # lxml inserts a doctype if none exists, so only include it in
            # the root if it was in the original html.
            root = tree if stripped.startswith(tree.docinfo.doctype) else page

        assert page is not None

        #
        # URLs
        #
        if self.base_url and not self.disable_link_rewrites:
            if not urlparse(self.base_url).scheme:
                raise ValueError("Base URL must have a scheme")
            for attr in ("href", "src"):
                for item in page.xpath("//@%s" % attr):
                    parent = item.getparent()
                    url = parent.attrib[attr]
                    if (
                        attr == "href"
                        and self.preserve_internal_links
                        and url.startswith("#")
                    ):
                        continue
                    if (
                        attr == "src"
                        and self.preserve_inline_attachments
                        and url.startswith("cid:")
                    ):
                        continue
                    if attr == "href" and url.startswith("tel:"):
                        continue
                    parent.attrib[attr] = urljoin(self.base_url, url)

        if hasattr(html, "getroottree"):
            return root
        else:
            kwargs.setdefault("method", self.method)
            kwargs.setdefault("pretty_print", pretty_print)
            kwargs.setdefault("encoding", "utf-8")  # As Ken Thompson intended
            out = etree.tostring(root, **kwargs).decode(kwargs["encoding"])

            return out
