import os
import re
from importlib import import_module
from ipaddress import ip_address
from urllib.parse import urljoin, urlparse

from django.template import Context, Template
from django.template.loader import get_template
from lxml import etree
from node_edge import NodeEngine


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


def stash_django_tags(source: str) -> tuple[str, list[str]]:
    """
    Replace every Django template tag/variable with a numbered placeholder so
    that the MJML compiler (which expects XML) does not choke on them.
    """
    tags: list[str] = []

    def _stash(m: re.Match) -> str:
        placeholder = f"__DJANGO_TAG_{len(tags)}__"
        tags.append(m.group(0))
        return placeholder

    safe_source = re.sub(r"\{[{%][^}]*?[}%]\}", _stash, source)
    return safe_source, tags


def restore_django_tags(html: str, tags: list[str]) -> str:
    """
    Restore placeholders created by stash_django_tags.
    """
    for index, tag in enumerate(tags):
        html = html.replace(f"__DJANGO_TAG_{index}__", tag)
    return html


def rewrite_urls(html: str, base_url: str) -> str:
    """
    Rewrite relative href/src URLs in HTML to absolute URLs using base_url.
    Skips fragment-only (#), cid:, and tel: links.
    """

    if not base_url:
        return html
    if not urlparse(base_url).scheme:
        raise ValueError("Base URL must have a scheme")

    stripped = html.strip()
    parser = etree.HTMLParser()
    tree = etree.fromstring(stripped, parser).getroottree()
    page = tree.getroot()
    root = tree if stripped.startswith(tree.docinfo.doctype) else page

    for attr in ("href", "src"):
        for item in page.xpath("//@%s" % attr):
            parent = item.getparent()
            url = parent.attrib[attr]
            if url.startswith("#"):
                continue
            if url.startswith("cid:"):
                continue
            if attr == "href" and url.startswith("tel:"):
                continue
            parent.attrib[attr] = urljoin(base_url, url)

    return etree.tostring(root, method="html", pretty_print=True, encoding="utf-8").decode("utf-8")


def render_mjml_to_html(template_path: str, context_dict: dict, base_url: str) -> str:
    """
    Renders an MJML template to HTML using node_edge.
    It delegates <mj-include> resolution to MJML natively via 'filePath',
    and safely stashes Django tags before compilation.
    """
    tpl = get_template(template_path)
    tpl_dir = os.path.dirname(tpl.origin.name)

    with open(tpl.origin.name, encoding="utf-8") as f:
        mjml_source = f.read()

    # Convert relative paths in includes to absolute paths and inline their content
    import re as regex_module
    def inline_include(match):
        path_attr = match.group(1)
        # Extract the path value
        path_match = regex_module.search(r'path=["\']([^"\']+)["\']', path_attr)
        if path_match:
            rel_path = path_match.group(1)
            abs_path = os.path.abspath(os.path.join(tpl_dir, rel_path))
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # If it's a CSS file, wrap it in <mj-style> tags
                    if abs_path.endswith('.css'):
                        content = f"<mj-style>{content}</mj-style>"

                    return content
                except Exception:
                    return match.group(0)
            else:
                return match.group(0)
        return match.group(0)

    mjml_source = regex_module.sub(r'<mj-include\s+([^>]*)>', inline_include, mjml_source)

    # 1. Stash Django tags to protect them from MJML validation
    mjml_safe, stashed_tags = stash_django_tags(mjml_source)

    # 2. Compile with MJML (allowing native includes via filePath)
    with NodeEngine({"dependencies": {"mjml": "^5.1.0"}}) as engine:
        mjml_fn = engine.import_from("mjml")
        mjml_render = mjml_fn(
            mjml_safe,
            {
                "minify": False,
                "validationLevel": "soft",
                "filePath": tpl_dir,
            },
        )
        compiled_html = str(mjml_render.html)

    # 3. Restore Django tags (this restores {% load %} and other logic)
    compiled_html = restore_django_tags(compiled_html, stashed_tags)

    # 4. Render through Django template engine.
    # {% load %} tags that appear outside <mjml>...</mjml> are silently
    # dropped by the MJML compiler (it only outputs the rendered body).
    # We collect all {% load %} tags from the original source and prepend
    # them so templatetag libraries are always available when Django parses
    # the compiled HTML.
    load_tags = [tag for tag in stashed_tags if re.match(r'\{%-?\s*load\s', tag)]
    if load_tags:
        compiled_html = "\n".join(load_tags) + "\n" + compiled_html

    ctx = Context(context_dict)
    html = Template(compiled_html).render(ctx)

    # 5. Rewrite relative URLs to absolute
    result = rewrite_urls(html, base_url)
    return result