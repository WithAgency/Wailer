from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Mapping, Sequence, Union
from urllib.parse import urljoin

from django.conf import settings
from django.template.loader import render_to_string
from phonenumbers import PhoneNumber, parse
from premailer import transform

from .errors import WailerTemplateException
from .utils import is_loopback

if TYPE_CHECKING:
    from .models import BaseMessage


JsonType = Union[
    str,
    int,
    float,
    bool,
    None,
    Mapping[str, "JsonType"],
    Sequence["JsonType"],
]


class BaseMessageType(ABC):
    """
    Common stuff between SMS and Email
    """

    def __init__(self, message: "BaseMessage"):
        self.message: "BaseMessage" = message

    @property
    def data(self) -> JsonType:
        """
        Shortcut to access the message's data
        """

        return self.message.data

    @property
    def context(self) -> JsonType:
        """
        Shortcut to access the message's context
        """

        return self.message.context

    @abstractmethod
    def get_locale(self) -> str:  # pragma: no cover
        """
        You must implement this to indicate which locale this message will be
        sent with. The locale will be set to this during all subsequent calls
        (by example while rendering templates).

        Let's note that the message's context is NOT available at this stage
        so you should definitely not rely on it. You can use self.data though.
        """

        raise NotImplementedError

    @abstractmethod
    def get_context(self) -> Mapping[str, JsonType]:  # pragma: no cover
        """
        You must implement this method in order to provide a context for your
        templates when they get rendered.

        It's important to mention that this method will be called only once at
        the time of creation of this email. Indeed, emails are immutable once
        sent so there is no reason that the context should change between
        calls. This prevents from having the content of the email changing.

        As a result, the value out of this function will be stored into DB and
        must be JSON-serializable.

        This function is called within the locale returned by
        :py:meth:`BaseMessageType.get_locale`
        """

        raise NotImplementedError

    def get_base_url(self) -> str:
        """
        Guesses the base URL for all links and images inside the email. This
        uses several strategies:

        #. If there is a `WAILER_BASE_URL` declared in the settings then we're
           just going to use that

        #. Otherwise we turn to the sites framework (if installed)

           * The `WAILER_SITE_ID` can force the ID of the site we're using

           * Which falls back to the default site. Since we don't have a
             guarantee to be running in a request here, you better be careful
             with that

           * To be noted that the scheme is determined automatically. If the
             domain is local then it's HTTP and otherwise it's HTTPS. That is
             not covering 100% of the cases but if you feel like you need
             something more precise feel free to set WAILER_BASE_URL or to
             override this method

        #. Otherwise we just fail because there is now ay to guess

        You can override this method to implement whatever behavior you desire
        instead of this one.
        """

        if hasattr(settings, "WAILER_BASE_URL"):
            return settings.WAILER_BASE_URL
        elif "django.contrib.sites" in settings.INSTALLED_APPS:
            from django.contrib.sites.models import Site

            if site_id := getattr(settings, "WAILER_SITE_ID", None):
                site = Site.objects.get(pk=site_id)
            else:
                site = Site.objects.get_current()

            host = site.domain.split(":")[0]

            if is_loopback(host):
                scheme = "http"
            else:
                scheme = "https"

            return f"{scheme}://{site.domain}"
        else:
            raise WailerTemplateException("Cannot determine absolute URL of website")


class SmsType(BaseMessageType, ABC):
    @abstractmethod
    def get_content(self) -> str:  # pragma: no cover
        """
        Implement this to return the text content of the SMS
        """

        raise NotImplementedError

    @abstractmethod
    def get_to(self) -> PhoneNumber:  # pragma: no cover
        """
        Implement this to return the phone number to which the SMS must be sent
        to.
        """

        raise NotImplementedError

    @abstractmethod
    def get_from(self) -> str:  # pragma: no cover
        """
        Returns an ID for your SMS sender. That's probably dependent on what
        your provider(s) will accept. Up to you!
        """

        raise NotImplementedError

    def make_absolute(self, url: str):
        """
        Convenience function to transform an URL into something absolute with
        the same logic as for emails.

        Parameters
        ----------
        url
            Any URL
        """

        return urljoin(self.get_base_url(), url)


class EmailType(BaseMessageType, ABC):
    """
    Implement this interface in order to provide your own email type.
    """

    @abstractmethod
    def get_to(self) -> str:  # pragma: no cover
        """
        Return here who you want to send that email to
        """

        raise NotImplementedError

    @abstractmethod
    def get_subject(self) -> str:  # pragma: no cover
        """
        Return here the subject of the email
        """

        raise NotImplementedError

    @abstractmethod
    def get_template_html_path(self) -> str:  # pragma: no cover
        """
        Implement if you want a HTML part of the email. Or don't if you don't
        want. It's just that the email provider will usually enforce at least
        a HTML or a text content, so make sure to have at least one.
        """

        raise NotImplementedError

    @abstractmethod
    def get_template_text_path(self) -> str:
        """
        Implement if you want a text part of the email. Or don't if you don't
        want. It's just that the email provider will usually enforce at least
        a HTML or a text content, so make sure to have at least one.
        """

        raise NotImplementedError

    def get_from(self) -> str:
        """
        Defaulting to Django's default, override for something else
        """

        return settings.DEFAULT_FROM_EMAIL

    def get_text_content(self) -> str:
        """
        Renders the text template. Override if you want to render differently.
        If you override then you might not need
        :py:meth:`get_template_text_path` or :py:meth:`get_template_context`
        (but it's your call).
        """

        return render_to_string(
            self.get_template_text_path(), self.get_template_context()
        )

    def get_html_content(self) -> str:
        """
        Renders the HTML template. Override if you want to render differently.
        If you override then you might not need
        :py:meth:`get_template_html_path` or :py:meth:`get_template_context`
        (but it's your call).

        HTML is transformed using Premailer to do various email things like
        inlining the CSS and changing relative links to absolute links.
        """

        html = render_to_string(
            self.get_template_html_path(), self.get_template_context()
        )
        return transform(html, base_url=self.get_base_url())

    def get_template_context(self) -> Mapping:
        """
        The context of templates shall be the one from :py:meth:`get_context`,
        with on top of that a reference to the message object in case you need
        it.

        Feel free to override and add whatever you need, however I'm not too
        sure why you would do that. Better do things in :py:meth:`get_context`
        for the protection it offers.
        """

        return dict(self=self.message, **self.message.context)
