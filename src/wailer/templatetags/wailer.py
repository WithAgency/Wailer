from urllib.parse import urljoin

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.template import library
from django.template.loader import render_to_string
from django.urls import reverse

from ..errors import WailerTemplateException

register = library.Library()


def build_absolute_uri(url_path):
    """
    Build an absolute URI based on the BASE_URL setting.
    """

    base_url = getattr(settings, "WAILER_BASE_URL")
    return urljoin(base_url, url_path)


@register.simple_tag()
def email_style(path):
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
def email_pixel_url(context):
    """
    Returns the URL of the tracking pixel for the `email` found in context.

    :param context: Template context
    :return: an URL to the pixel
    """

    email = context["email"]
    return build_absolute_uri(
        reverse("wailer_pixel", kwargs={"email_uuid": email.uuid})
    )
