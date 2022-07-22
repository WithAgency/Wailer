from abc import ABC, abstractmethod
from typing import Any, Mapping
from django.conf import settings
from django.template.loader import render_to_string

from phonenumbers import PhoneNumber, parse

from wailer.errors import WailerSmsException
from premailer import transform
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .models import BaseMessage


class BaseMessageType(ABC):
    """
    Common stuff between SMS and Email
    """

    def __init__(self, message: "BaseMessage"):
        self.data: Any = message.data
        self.message: "BaseMessage" = message

    @abstractmethod
    def get_locale(self) -> str:
        """
        You must implement this to indicate which locale this message will be
        sent with. The locale will be set to this during all subsequent calls
        (by example while rendering templates).
        """

        raise NotImplementedError

    def get_data(self) -> Any:
        """
        Accessor for the data, in case someone wants to override it without
        dirty tricks. This data will be saved in a JSON field and will be used
        (through the message model) to instantiate this object. It's not
        supposed to be changed on the way, especially if you work with cached
        properties.
        """

        return self.data


class SmsType(BaseMessageType, ABC):
    @abstractmethod
    def get_content(self) -> str:
        """
        Implement this to return the text content of the SMS
        """

        raise NotImplementedError

    @abstractmethod
    def get_to(self) -> PhoneNumber:
        """
        Implement this to return the phone number to which the SMS must be sent
        to.
        """

        raise NotImplementedError

    def get_from(self) -> PhoneNumber:
        """
        Guesses the sender number based on the "to" number's country. Feel free
        to override this method to change this behaviour if you need to (but
        the default behaviour should make sense).
        """

        for num in settings.WAILER_SMS_SENDERS:
            sender = parse(num)

            if sender.country_code == self.get_to().country_code:
                return sender


class EmailType(BaseMessageType, ABC):
    """
    Interface for an email type
    """

    def get_from(self) -> str:
        """
        Defaulting to Django's default, override for something else
        """

        return settings.DEFAULT_FROM_EMAIL

    @abstractmethod
    def get_to(self) -> str:
        """
        Return here who you want to send that email to
        """

        raise NotImplementedError

    @abstractmethod
    def get_subject(self) -> str:
        """
        Return here the subject of the email
        """

        raise NotImplementedError

    def get_text_content(self) -> str:
        """
        Renders the text template. Override if you want to render differently.
        If you override then you might not need get_template_text_path() or
        get_template_context() (but it's your call).
        """

        return render_to_string(
            self.get_template_text_path(), self.get_template_context()
        )

    def get_html_content(self) -> str:
        """
        Renders the HTML template. Override if you want to render differently.
        If you override then you might not need get_template_html_path() or
        get_template_context() (but it's your call).

        HTML is transformed using Premailer to do various email things like
        inlining the CSS and changing relative links to absolute links.
        """

        html = render_to_string(
            self.get_template_html_path(), self.get_template_context()
        )
        return transform(html, base_url=settings.FRONT_URL)

    def get_template_context(self) -> Mapping:
        """
        Default sensible context for template renderings, feel free to add
        stuff in there.
        """

        return dict(self=self.message)

    def get_template_html_path(self) -> str:
        """
        Implement if you want a HTML part of the email. Or don't if you don't
        want. It's just that the email provider will usually enforce at least
        a HTML or a text content, so make sure to have at least one.
        """

        raise NotImplementedError

    def get_template_text_path(self) -> str:
        """
        Implement if you want a text part of the email. Or don't if you don't
        want. It's just that the email provider will usually enforce at least
        a HTML or a text content, so make sure to have at least one.
        """

        raise NotImplementedError
