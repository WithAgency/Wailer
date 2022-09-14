import base64
from email.utils import parseaddr
from typing import Iterator, List, Mapping, Sequence, Tuple, TypedDict, Union

import httpx
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.mail.backends.base import BaseEmailBackend
from django.utils.encoding import force_bytes
from sms.backends.base import BaseSmsBackend
from sms.message import Message as SmsMessage
from typing_extensions import NotRequired

from ._utils import by_alternatives

HEADERS_BLACKLIST = set(
    x.lower()
    for x in [
        "From",
        "Sender",
        "Subject",
        "To",
        "Cc",
        "Bcc",
        "Return-Path",
        "Delivered-To",
        "DKIM-Signature",
        "DomainKey-Status",
        "Received-SPF",
        "Authentication-Results",
        "Received",
        "X-Mailjet-Prio",
        "X-Mailjet-Debug",
        "User-Agent",
        "X-Mailer",
        "X-MJ-CustomID",
        "X-MJ-EventPayload",
        "X-MJ-Vars",
        "X-MJ-TemplateErrorDeliver",
        "X-MJ-TemplateErrorReporting",
        "X-MJ-TemplateLanguage",
        "X-Mailjet-TrackOpen",
        "X-Mailjet-TrackClick",
        "X-MJ-TemplateID",
        "X-MJ-WorkflowID",
        "X-Feedback-Id",
        "X-Mailjet-Segmentation",
        "List-Id",
        "X-MJ-MID",
        "X-MJ-ErrorMessage",
        "Date",
        "X-CSA-Complaints",
        "Message-Id",
        "X-Mailjet-Campaign",
        "X-MJ-StatisticsContactsListID",
    ]
)


def parse_email_address(address: str) -> "EmailAddress":
    """
    Parses an email address into a Mailjet format.

    >>> assert parse_email_address("Foo <foo@bar.com>") == dict(
    >>>     Name="Foo",
    >>>     Email="foo@bar.com",
    >>> )

    Parameters
    ----------
    address
        E-mail address to be parsed
    """

    name, addr = parseaddr(address)

    if not addr:
        raise ValueError(f"Invalid e-mail format: {address}")

    out = dict(Email=addr)

    if name:
        out["Name"] = name

    return out


def convert_attachment(attachment: Tuple[str, bytes, str]) -> "Attachment":
    """
    Converts an attachment into the Mailjet expected format

    Parameters
    ----------
    attachment
        An item of email.attachments
    """

    return Attachment(
        Filename=attachment[0],
        ContentType=attachment[2],
        Base64Content=base64.b64encode(force_bytes(attachment[1])).decode(),
    )


class EmailAddress(TypedDict):
    Email: str
    Name: str


class Attachment(TypedDict):
    ContentType: str
    Filename: str
    Base64Content: str


class Message(TypedDict):
    From: EmailAddress
    To: List[EmailAddress]
    Cc: NotRequired[List[EmailAddress]]
    Bcc: NotRequired[List[EmailAddress]]
    Subject: str
    TextPart: NotRequired[str]
    HTMLPart: NotRequired[str]
    Attachments: NotRequired[List[Attachment]]
    Headers: NotRequired[Mapping[str, str]]


class SendEmailRequest(TypedDict):
    Messages: List[Message]


class ToOutput(TypedDict):
    Email: str
    MessageUUID: str
    MessageID: int
    MessageHref: str


class MessageOutput(TypedDict):
    Status: str
    To: Sequence[ToOutput]


class SendEmailOutput(TypedDict):
    Messages: List[MessageOutput]


class SendSmsRequest(TypedDict):
    From: str
    To: str
    Text: str


class MailjetClient:
    """
    Mixin to help getting a HTTPX client pre-configured for Mailjet's API
    """

    @property
    def base_url(self):
        """
        That shouldn't change but still making it configurable
        """

        return getattr(settings, "MAILJET_BASE_URL", "https://api.mailjet.com")

    def make_auth_client(self) -> httpx.Client:
        """
        Creating a HTTPX client with the base URL and the authentication
        already configured from Django settings to make sure that it's super
        easy to make HTTP queries.
        """

        return httpx.Client(
            base_url=self.base_url,
            auth=httpx.BasicAuth(
                settings.MAILJET_API_KEY_PUBLIC,
                settings.MAILJET_API_KEY_PRIVATE,
            ),
        )

    def make_bearer_client(self) -> httpx.Client:
        """
        Creating a HTTPX client with the base URL and the authentication
        already configured from Django settings to make sure that it's super
        easy to make HTTP queries.
        """

        return httpx.Client(
            base_url=self.base_url,
            headers=dict(Authorization=f"Bearer {settings.MAILJET_API_TOKEN}"),
        )


class MailjetEmailBackend(MailjetClient, BaseEmailBackend):
    """
    An email backend that will use Mailjet to send emails. The only feature of
    Mailjet that shouldn't be rendered properly is the inline attachments,
    because it seems there is no easy way to do this in Django (that I've
    found?).

    Emails are a mess, maybe (probably) some edge cases have been left out.
    """

    def make_message(
        self, message: Union[EmailMessage, EmailMultiAlternatives]
    ) -> Message:
        """
        Doing our best to guess from the EmailMessage what we should send to
        the API. If there are any edge cases, take care of them here.
        """

        by_alt = by_alternatives(message)

        out = Message(
            From=parse_email_address(message.from_email),
            To=[parse_email_address(x) for x in message.to],
            Subject=message.subject,
        )

        if text_message := by_alt.get("text/plain"):
            out["TextPart"] = text_message

        if html_message := by_alt.get("text/html"):
            out["HTMLPart"] = html_message

        if message.cc:
            out["Cc"] = [parse_email_address(x) for x in message.cc]

        if message.bcc:
            out["Bcc"] = [parse_email_address(x) for x in message.bcc]

        if message.attachments:
            out["Attachments"] = [convert_attachment(x) for x in message.attachments]

        headers = {
            k: v
            for k, v in message.extra_headers.items()
            if k.lower() not in HEADERS_BLACKLIST
        }

        if headers:
            out["Headers"] = headers

        return out

    def send_messages(self, email_messages: Sequence[EmailMultiAlternatives]) -> int:
        """
        Sends messages through the Mailjet API. The Django API expects to
        receive the sent emails count as an output which is why most exceptions
        are silenced here (kinda dumb if you ask me, but that's the way of the
        API).
        """

        payload = SendEmailRequest(
            Messages=[self.make_message(x) for x in email_messages]
        )

        with self.make_auth_client() as client:
            resp = client.post("/v3.1/send", json=payload)

            if not resp.is_success:
                return 0

        output: SendEmailOutput = resp.json()

        return sum(1 if x["Status"] == "success" else 0 for x in output["Messages"])


class MailjetSmsBackend(MailjetClient, BaseSmsBackend):
    """
    A Mailjet backend for Django-SMS
    """

    def make_message(self, message: SmsMessage) -> Iterator[SendSmsRequest]:
        """
        There is no bulk SMS send with Mailjet (or is there?) so we'll send
        and transform each message individually, including for each recipient.
        That's why for a single message input, you can get several requests
        going out.
        """

        for to in message.recipients:
            yield SendSmsRequest(
                From=message.originator,
                To=to,
                Text=message.body,
            )

    def send_messages(self, messages: List[SmsMessage]) -> int:
        """
        Transforming a list of messages into a list of requests to Mailjet
        to be able to send those to clients.
        """

        sent = 0

        with self.make_bearer_client() as client:
            for message in messages:
                for call in self.make_message(message):
                    resp = client.post("/v4/sms-send", json=call)

                    if resp.is_success:
                        sent += 1

        return sent
