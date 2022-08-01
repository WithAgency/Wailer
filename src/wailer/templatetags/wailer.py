from typing import Mapping, TypedDict, Union
from urllib.parse import urljoin

from django.contrib.staticfiles.finders import find
from django.template import library
from django.template.defaulttags import URLNode
from django.template.defaulttags import url as django_url
from django.template.loader import render_to_string

from ..errors import WailerTemplateException
from ..models import Email

register = library.Library()


class WailerContext(TypedDict):
    self: Email


class AbsoluteUrlNode(URLNode):
    def render(self, context: Union[Mapping, WailerContext]) -> str:
        out = super().render(context)

        if self.asvar:
            url = context[self.asvar]
        else:
            url = out

        new_url = urljoin(context["self"].base_url, url)

        if self.asvar:
            context[self.asvar] = new_url  # noqa
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
        raise WailerTemplateException(f'Style file "{path}" cannot be found')

    with open(real_path, encoding="utf-8") as f:
        content = f.read()

    return render_to_string("wailer/style.html", dict(content=content))


@register.simple_tag(takes_context=True)
def make_absolute(context: WailerContext, path: str) -> str:
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
