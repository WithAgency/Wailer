"""Template tags to help rendering emails (absolute URLs, inline styles)."""

from pathlib import Path
from urllib.parse import urljoin

from django.contrib.staticfiles.finders import find
from django.template import Context, library
from django.template.defaulttags import URLNode
from django.template.defaulttags import url as django_url
from django.template.loader import render_to_string

from ..errors import WailerTemplateException

register = library.Library()


class AbsoluteUrlNode(URLNode):
    """A URL node that makes the resolved URL absolute."""

    def render(self, context: Context) -> str:
        """Render the URL and make it absolute using the email's base URL."""
        out = super().render(context)

        if self.asvar:
            url = context[self.asvar]
        else:
            url = out

        new_url = urljoin(context["self"].base_url, url)

        if self.asvar:
            context[self.asvar] = new_url
            return ""
        else:
            return new_url


@register.simple_tag()
def email_style(path: str) -> str:
    """
    Dumps a CSS file directly into
    """

    real_path = find(path)

    if not real_path:
        msg = f'Style file "{path}" cannot be found'
        raise WailerTemplateException(msg)

    content = Path(real_path).read_text(encoding="utf-8")

    return render_to_string("wailer/style.html", dict(content=content))


@register.simple_tag(takes_context=True)
def make_absolute(context: Context, path: str) -> str:
    """
    Given the path, returns an absolute URL (for this email's base URL)

    Parameters
    ----------
    context
        Template context
    path
        Path to make absolute
    """

    self = context["self"]

    return urljoin(self.base_url, path)


@register.tag
def absolute_url(parser, token):
    """
    Wrapper around Django's :code:`url` tag that will make all returned URLs
    absolute.
    """

    node = django_url(parser, token)

    return AbsoluteUrlNode(node.view_name, node.args, node.kwargs, node.asvar)
