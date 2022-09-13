from typing import Mapping

from django.utils.translation import gettext_lazy as _
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
