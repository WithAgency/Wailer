"""MJML rendering tests.

MJML 5 changed a lot under the hood (async render function, dropped core
minify option, different HTML output) so this checks in depth that the
rendering pipeline — MJML render then MjmlPremailer URL rewriting — still
behaves: custom CSS survives, relative URLs become absolute, anchors and
tel: links stay untouched.
"""

import pytest
from django.core import mail
from django.test import override_settings

from wailer.models import Email

pytestmark = pytest.mark.django_db(transaction=True)

FANCY_DATA = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.org",
    "locale": "en",
}


@pytest.fixture
def fancy_html():
    """Send the fancy MJML email and return its rendered HTML body."""
    with override_settings(WAILER_BASE_URL="https://example.org"):
        Email.send("fancy-mjml", FANCY_DATA)

    assert len(mail.outbox) == 1
    alternatives = mail.outbox[0].alternatives
    assert len(alternatives) == 1

    content, mime = alternatives[0]
    assert mime == "text/html"

    return content


def test_mjml_renders_html(fancy_html):
    assert "<html" in fancy_html
    assert "Hello, John Doe!" in fancy_html


def test_mjml_keeps_custom_css(fancy_html):
    # The <mj-style> block must survive rendering (MjmlPremailer must NOT
    # inline or strip it: MJML deals with CSS itself)
    assert ".fancy-link a" in fancy_html
    assert "#ff0042" in fancy_html
    # And the class must still be on the element
    assert "fancy-link" in fancy_html


def test_mjml_absolutizes_relative_links(fancy_html):
    assert 'href="https://example.org/promo"' in fancy_html
    assert 'href="/promo"' not in fancy_html


def test_mjml_absolutizes_image_sources(fancy_html):
    assert 'src="https://example.org/static/my_app/logo.png"' in fancy_html
    assert 'src="/static/my_app/logo.png"' not in fancy_html


def test_mjml_preserves_anchor_links(fancy_html):
    assert 'href="#anchor"' in fancy_html


def test_mjml_preserves_tel_links(fancy_html):
    assert 'href="tel:+34600000000"' in fancy_html


def test_mjml_output_is_responsive_email(fancy_html):
    # Sanity check that this is real MJML output, not the raw template
    assert "<mjml>" not in fancy_html
    assert "@media" in fancy_html


def test_mjml_invalid_template_raises():
    """With validationLevel=strict, an invalid MJML template must raise."""
    from node_edge import JavaScriptError, NodeEngine

    with NodeEngine({"dependencies": {"mjml": "^5.4.0"}}) as engine:
        mjml = engine.import_from("mjml")

        with pytest.raises(JavaScriptError):
            engine.resolve(
                mjml(
                    "<mjml><mj-body><mj-bogus /></mj-body></mjml>",
                    {"validationLevel": "strict"},
                )
            )
