from django.contrib.staticfiles.finders import find
from django.template import library
from django.template.loader import render_to_string

from ..errors import WailerTemplateException

register = library.Library()


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
