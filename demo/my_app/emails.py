from typing import Mapping

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from my_app.models import User

from wailer.interfaces import EmailType, JsonType


class Static(EmailType):
    """
    An email with purely static content just to test the sending
    """

    def get_to(self) -> str:
        return "foo@bar.com"

    def get_subject(self) -> str:
        return "Static Subject"

    def get_context(self) -> Mapping[str, JsonType]:
        return dict(prefix="Static")

    def get_template_html_path(self) -> str:
        return "my_app/wailer/static.html"

    def get_template_text_path(self) -> str:
        return "my_app/wailer/static.txt"

    def get_locale(self) -> str:
        return "fr"


class StaticNoText(Static):
    def get_template_text_path(self) -> str:
        raise NotImplementedError


class StaticNoHtml(Static):
    def get_template_html_path(self) -> str:
        raise NotImplementedError


class Hello(EmailType):
    """
    A nice email to say hello to people
    """

    def get_to(self) -> str:
        return self.data["email"]

    def get_locale(self) -> str:
        return self.data["locale"]

    def get_context(self) -> Mapping[str, JsonType]:
        return dict(
            name=f"{self.data['first_name']} {self.data['last_name']}",
        )

    def get_subject(self) -> str:
        return _(f"Hello %(name)s") % dict(name=self.context["name"])

    def get_template_html_path(self) -> str:
        return "my_app/wailer/hello.html"

    def get_template_text_path(self) -> str:
        return "my_app/wailer/hello.txt"


class HelloMjml(Hello):
    """
    Same concept as the Hello mail except it's rendered from MJML
    """

    def get_template_html_path(self) -> str:
        return "my_app/wailer/hello.mjml"


class HelloUser(Hello):
    """
    The same as Hello, however with live data from a user to demonstrate how
    things need to be frozen in the context
    """

    @cached_property
    def user(self):
        return User.objects.get(pk=self.data["user_id"])

    def get_to(self) -> str:
        return self.user.email

    def get_context(self) -> Mapping[str, JsonType]:
        return dict(
            name=f"{self.user.first_name} {self.user.last_name}",
            locale=self.user.locale,
        )

    def get_locale(self) -> str:
        return self.context["locale"]


class StyledHtml(Static):
    def get_template_html_path(self) -> str:
        return "my_app/wailer/styled-html.html"


class AbsoluteUrlStraight(Static):
    def get_template_html_path(self) -> str:
        raise NotImplementedError

    def get_template_text_path(self) -> str:
        return "my_app/wailer/absolute-url-straight.txt"


class AbsoluteUrlAs(Static):
    def get_template_html_path(self) -> str:
        raise NotImplementedError

    def get_template_text_path(self) -> str:
        return "my_app/wailer/absolute-url-as.txt"


class MakeAbsolute(Static):
    def get_template_html_path(self) -> str:
        raise NotImplementedError

    def get_template_text_path(self) -> str:
        return "my_app/wailer/make-absolute.txt"
