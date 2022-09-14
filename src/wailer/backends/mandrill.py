import base64
from email.utils import parseaddr
from enum import Enum
from typing import List, Mapping, Sequence, Tuple, TypedDict, Union

import httpx
from django.conf import settings
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.mail.backends.base import BaseEmailBackend
from django.utils.encoding import force_bytes
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
        "User-Agent",
        "List-Id",
        "Date",
        "X-CSA-Complaints",
        "Message-Id",
    ]
)


def parse_email_address(address: str, email_type: "EmailType") -> "EmailAddress":
    """
    Parses an email address into a Mandrill format.

    >>> assert parse_email_address("Foo <foo@bar.com>", EmailType.to) == dict(
    >>>     name="Foo",
    >>>     email="foo@bar.com",
    >>>     type="to",
    >>> )

    Parameters
    ----------
    address
        E-mail address to be parsed
    email_type
        Type of email to embed in the output
    """

    name, addr = parseaddr(address)

    if not addr:
        raise ValueError(f"Invalid e-mail format: {address}")

    out = EmailAddress(email=addr, type=email_type.value)  # noqa

    if name:
        out["name"] = name

    return out


def convert_attachment(attachment: Tuple[str, bytes, str]) -> "Attachment":
    """
    Converts an attachment into the Mandrill expected format

    Parameters
    ----------
    attachment
        An item of email.attachments
    """

    return Attachment(
        name=attachment[0],
        type=attachment[2],
        content=base64.b64encode(force_bytes(attachment[1])).decode(),
    )


class EmailType(Enum):
    to = "to"
    cc = "cc"
    bcc = "bcc"


class EmailAddress(TypedDict):
    email: str
    type: str
    name: NotRequired[str]


class Attachment(TypedDict):
    type: str
    name: str
    content: str


class Message(TypedDict):
    from_email: str
    from_name: NotRequired[str]
    to: List[EmailAddress]
    subject: str
    text: NotRequired[str]
    html: NotRequired[str]
    attachments: NotRequired[List[Attachment]]
    headers: NotRequired[Mapping[str, str]]


class SendEmailRequest(TypedDict):
    message: Message
    key: str


class SentOutput(TypedDict):
    email: str
    status: str
    reject_reason: NotRequired[str]
    _id: NotRequired[str]


class MandrillEmailBackend(BaseEmailBackend):
    """
    An email backend that will use Mandrill to send emails. There are many
    flags that can be set upon sending an email and we're setting very little
    of them. In the future this could be extended but those flags aren't found
    in standard email objects so we'd have to find a way to pass them through.

    Emails are a mess, maybe (probably) some edge cases have been left out.
    """

    @property
    def base_url(self):
        """
        That shouldn't change but still making it configurable
        """

        return getattr(settings, "MANDRILL_BASE_URL", "https://mandrillapp.com")

    @property
    def api_key(self):
        """
        Shortcut to get the API key from the settings
        """

        return settings.MANDRILL_API_KEY

    def make_client(self) -> httpx.Client:
        """
        Making a HTTPX client, even though since the API key is put in the POST
        body the utility of this is a bit dull
        """

        return httpx.Client(base_url=self.base_url)

    def make_message(
        self, message: Union[EmailMessage, EmailMultiAlternatives]
    ) -> Message:
        """
        Doing our best to guess from the EmailMessage what we should send to
        the API. If there are any edge cases, take care of them here.
        """

        by_alt = by_alternatives(message)
        from_name, from_email = parseaddr(message.from_email)
        to = []

        for email_type in EmailType:
            for target in getattr(message, email_type.value, []):  # noqa
                to.append(parse_email_address(target, email_type))

        out = Message(
            from_email=from_email,
            **(dict(from_name=from_name) if from_name else {}),
            to=to,
            subject=message.subject,
        )

        if text_message := by_alt.get("text/plain"):
            out["text"] = text_message

        if html_message := by_alt.get("text/html"):
            out["html"] = html_message

        if message.attachments:
            out["attachments"] = [convert_attachment(x) for x in message.attachments]

        headers = {
            k: v
            for k, v in message.extra_headers.items()
            if k.lower() not in HEADERS_BLACKLIST
        }

        if headers:
            out["headers"] = headers

        return out

    def send_messages(self, email_messages: Sequence[EmailMultiAlternatives]) -> int:
        """
        Sends messages through the Mandrill API. The Django API expects to
        receive the sent emails count as an output which is why most exceptions
        are silenced here (kinda dumb if you ask me, but that's the way of the
        API).
        """

        done = 0

        with self.make_client() as client:
            for message in email_messages:
                payload = SendEmailRequest(
                    key=self.api_key,
                    message=self.make_message(message),
                )

                resp = client.post("/api/1.0/messages/send", json=payload)
                data: List[SentOutput] = resp.json()

                if resp.is_success and all(x["status"] == "sent" for x in data):
                    done += 1

        return done
