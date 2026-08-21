"""Models storing sent emails and SMSes."""

from typing import Any
from uuid import uuid4

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import override as override_locale
from phonenumber_field.modelfields import PhoneNumberField
from sms import send_sms

from .errors import WailerException
from .interfaces import EmailType, JsonType, SmsType
from .utils import import_class


class BaseMessage(models.Model):
    """
    Common fields between emails and SMSs
    """

    class Meta:
        abstract = True

    id = models.UUIDField(default=uuid4, primary_key=True)
    for_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.CASCADE,
        related_name="+",
    )
    data = models.JSONField()
    context = models.JSONField()
    type = models.CharField(max_length=1000)
    date_created = models.DateTimeField(auto_now_add=True)
    date_sent = models.DateTimeField(null=True, blank=True)


class Email(BaseMessage):
    """
    Sent emails and a way to recompose/re-render them.
    """

    sender = models.EmailField(max_length=1000)
    recipient = models.EmailField(max_length=1000)

    @classmethod
    def send(
        cls,
        type_: str,
        data: JsonType,
        user: models.Model | None = None,
    ) -> "Email":
        """
        Call this to immediately send the email with the appropriate data.

        The type must be registered in the WAILER_EMAIL_TYPES settings and
        must implement the EmailType interface.

        Parameters
        ----------
        type_
            Name of the registered email type
        data
            Data that the email type will be using, but also that will be
            saved into DB for restitution later (so must be serializable to
            JSON).
        user
            User concerned by this email. Not mandatory but it's recommended
            to fill it up when sending an email to a user from the DB so that
            it's easy to delete emails (and thus their content) associated to
            this user when they delete their account or exert any kind of
            GDPR rights.
        """

        if type_ not in settings.WAILER_EMAIL_TYPES:
            msg = f"Email type {type_!r} is not declared in WAILER_EMAIL_TYPES"
            raise WailerException(msg)

        # AUTH_USER_MODEL is dynamic; a reusable lib cannot reference the
        # concrete user model that django-stubs resolves here.
        obj = Email(  # type: ignore[misc]
            data=data,
            type=type_,
            for_user=user,
        )

        obj.sender = obj.email.get_from()
        obj.recipient = obj.email.get_to()
        obj.context = obj.email.get_context()

        obj.save()

        obj.send_now()

        return obj

    @cached_property
    def email(self) -> EmailType:
        """
        Generates the email "type" object from this model
        """

        if self.type not in settings.WAILER_EMAIL_TYPES:
            msg = f"Email type {self.type!r} is not declared in WAILER_EMAIL_TYPES"
            raise WailerException(msg)

        type_class: type[EmailType] = import_class(
            settings.WAILER_EMAIL_TYPES[self.type]
        )

        if not type_class:
            msg = f"Could not import class for email type {self.type!r}"
            raise WailerException(msg)

        return type_class(self)

    @cached_property
    def base_url(self) -> str:
        """
        A shortcut to get the underlying email's base URL
        """

        return self.email.get_base_url()

    @cached_property
    def link_html(self):
        """
        Returns a relative link for this email to be seen in a browser in HTML
        format. Useful for debugging and for inclusion in said emails.
        """

        return reverse("view_email", kwargs=dict(email_uuid=f"{self.pk}", fmt="html"))

    @cached_property
    def link_text(self):
        """
        Returns a relative link for this email to be seen in a browser in text
        format. Useful for debugging and for inclusion in said emails.
        """

        return reverse("view_email", kwargs=dict(email_uuid=f"{self.pk}", fmt="txt"))

    def send_now(self):
        """
        Sends the email now. Called under the hood by send(). The `_now` part
        suggests that there will maybe be a `_later` strategy but not yet (nor
        ever?)
        """

        locale = self.email.get_locale()

        with override_locale(locale):
            self.recipient = self.email.get_to()
            self.sender = self.email.get_from()

            try:
                text_content = self.email.get_text_content()
            except NotImplementedError:
                text_content = None

            try:
                html_content = self.email.get_html_content()
            except NotImplementedError:
                html_content = None

            mail = EmailMultiAlternatives(
                subject=self.email.get_subject(),
                body=text_content,
                from_email=self.email.get_from(),
                to=[self.email.get_to()],
            )

            if html_content:
                mail.attach_alternative(html_content, "text/html")

            for attachment in self.email.get_attachments():
                mail.attach(*attachment)

            mail.send()

            Email.objects.filter(pk=self.pk).update(
                date_sent=now(), recipient=self.recipient, sender=self.sender
            )


class Sms(BaseMessage):
    """An SMS that was sent or is about to be sent."""

    sender = models.CharField(
        default="",
        blank=True,
        max_length=100,
    )
    recipient = PhoneNumberField()

    @classmethod
    def send(
        cls,
        type_: str,
        data: Any,
        user: models.Model | None = None,
    ):
        """
        Call this to immediately send the SMS with the appropriate data.

        The type must be registered in the WAILER_SMS_TYPES settings and
        must implement the EmailType interface.

        Parameters
        ----------
        type_
            Name of the registered SMS type
        data
            Data that the SMS type will be using, but also that will be
            saved into DB for restitution later (so must be serializable to
            JSON).
        user
            User concerned by this SMS. Not mandatory but it's recommended
            to fill it up when sending an email to a user from the DB so that
            it's easy to delete emails (and thus their content) associated to
            this user when they delete their account or exert any kind of
            GDPR rights.
        """

        if type_ not in settings.WAILER_SMS_TYPES:
            msg = f"SMS type {type_!r} is not declared in WAILER_SMS_TYPES"
            raise WailerException(msg)

        # AUTH_USER_MODEL is dynamic; a reusable lib cannot reference the
        # concrete user model that django-stubs resolves here.
        obj = Sms(  # type: ignore[misc]
            data=data,
            type=type_,
            for_user=user,
        )

        obj.sender = obj.sms.get_from()
        obj.recipient = obj.sms.get_to()
        obj.context = obj.sms.get_context()

        obj.save()

        obj.send_now()

        return obj

    @cached_property
    def sms(self) -> SmsType:
        """
        Generates the SMS "type" object from this model
        """

        if self.type not in settings.WAILER_SMS_TYPES:
            msg = f"SMS type {self.type!r} is not declared in WAILER_SMS_TYPES"
            raise WailerException(msg)

        type_class: type[SmsType] = import_class(settings.WAILER_SMS_TYPES[self.type])

        if not type_class:
            msg = f"Could not import class for SMS type {self.type!r}"
            raise WailerException(msg)

        return type_class(self)

    def send_now(self):
        """
        Sends the SMS now. Called under the hood by send(). The `_now` part
        suggests that there will maybe be a `_later` strategy but not yet (nor
        ever?)
        """

        locale = self.sms.get_locale()

        with override_locale(locale):
            self.recipient = self.sms.get_to()
            self.sender = self.sms.get_from()
            send_sms(
                body=self.sms.get_content(),
                originator=f"{self.sender or ''}",
                recipients=[f"{self.recipient}"],
            )
            Sms.objects.filter(pk=self.pk).update(
                date_sent=now(), recipient=self.recipient, sender=self.sender
            )
