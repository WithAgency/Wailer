from typing import Mapping

from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from my_app.models import User
from phonenumbers import PhoneNumber, parse

from wailer.interfaces import JsonType, SmsType


class Hello(SmsType):
    """
    A static Hello message
    """

    def get_context(self) -> Mapping[str, JsonType]:
        return {"word": "World", **self.data}

    def get_content(self) -> str:
        return _("Hello %(word)s!") % self.context

    def get_to(self) -> PhoneNumber:
        return parse("+34659424242")

    def get_from(self) -> str:
        return "Wailer"

    def get_locale(self) -> str:
        return "fr"


class HelloUser(SmsType):
    """
    A nice SMS to say hello to people
    """

    def get_from(self) -> str:
        return "Wailer"

    @cached_property
    def user(self):
        return User.objects.get(pk=self.data["user_id"])

    def get_content(self) -> str:
        return _("Hello %(name)s") % dict(name=self.context["name"])

    def get_to(self) -> str:
        return self.user.phone_number

    def get_context(self) -> Mapping[str, JsonType]:
        return dict(
            name=f"{self.user.first_name} {self.user.last_name}",
            locale=self.user.locale,
        )

    def get_locale(self) -> str:
        return self.context["locale"]


class ComeHomeUser(HelloUser):
    """
    Same as the HelloUser but demonstrating how to get an absolute URL
    """

    def get_content(self) -> str:
        return _("Hello %(name)s, come home to: %(url)s") % dict(
            name=self.context["name"],
            url=self.make_absolute("/"),
        )
