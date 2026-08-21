"""HTTP-level tests for the Mailjet and Mandrill backends.

The remote APIs are simulated with pytest-httpx: the real backend code runs
and its actual outgoing requests (URL, auth, payload) are verified at the
network level.
"""

import base64
import json

from django.core.mail import EmailMultiAlternatives
from django.test import override_settings
from sms import Message as SmsMessage

from wailer.backends import (
    MailjetEmailBackend,
    MailjetSmsBackend,
    MandrillEmailBackend,
)

MAILJET_SETTINGS = {
    "MAILJET_API_KEY_PUBLIC": "pub-key",
    "MAILJET_API_KEY_PRIVATE": "priv-key",
    "MAILJET_API_TOKEN": "sms-token",
}


def make_email() -> EmailMultiAlternatives:
    email = EmailMultiAlternatives(
        subject="Hi there",
        body="Text body",
        from_email="Sender <sender@example.org>",
        to=["Recipient <to@example.org>"],
        cc=["cc@example.org"],
        headers={"X-Custom": "yes", "Subject": "blacklisted"},
    )
    email.attach_alternative("<p>Html body</p>", "text/html")
    email.attach("file.txt", b"content", "text/plain")

    return email


@override_settings(**MAILJET_SETTINGS)
def test_mailjet_email_payload(httpx_mock):
    httpx_mock.add_response(
        url="https://api.mailjet.com/v3.1/send",
        json={"Messages": [{"Status": "success", "To": []}]},
    )

    sent = MailjetEmailBackend().send_messages([make_email()])

    assert sent == 1

    request = httpx_mock.get_request()
    assert request.method == "POST"

    # BasicAuth from the settings
    expected_auth = base64.b64encode(b"pub-key:priv-key").decode()
    assert request.headers["Authorization"] == f"Basic {expected_auth}"

    payload = json.loads(request.content)
    (message,) = payload["Messages"]

    assert message["From"] == {"Email": "sender@example.org", "Name": "Sender"}
    assert message["To"] == [{"Email": "to@example.org", "Name": "Recipient"}]
    assert message["Cc"] == [{"Email": "cc@example.org"}]
    assert message["Subject"] == "Hi there"
    assert message["TextPart"] == "Text body"
    assert message["HTMLPart"] == "<p>Html body</p>"
    assert message["Attachments"] == [
        {
            "Filename": "file.txt",
            "ContentType": "text/plain",
            "Base64Content": base64.b64encode(b"content").decode(),
        }
    ]
    # Blacklisted headers must be dropped, custom ones kept
    assert message["Headers"] == {"X-Custom": "yes"}


@override_settings(**MAILJET_SETTINGS)
def test_mailjet_email_failure_counts_zero(httpx_mock):
    httpx_mock.add_response(
        url="https://api.mailjet.com/v3.1/send",
        status_code=400,
        json={"ErrorMessage": "nope"},
    )

    assert MailjetEmailBackend().send_messages([make_email()]) == 0


@override_settings(**MAILJET_SETTINGS)
def test_mailjet_sms_payload(httpx_mock):
    httpx_mock.add_response(
        url="https://api.mailjet.com/v4/sms-send",
        json={},
        is_reusable=True,
    )

    message = SmsMessage(
        body="Hello!",
        originator="+34600000001",
        recipients=["+34600000002", "+34600000003"],
    )

    sent = MailjetSmsBackend().send_messages([message])

    # One request per recipient
    assert sent == 2

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert requests[0].headers["Authorization"] == "Bearer sms-token"

    payloads = [json.loads(r.content) for r in requests]
    assert payloads == [
        {"From": "+34600000001", "To": "+34600000002", "Text": "Hello!"},
        {"From": "+34600000001", "To": "+34600000003", "Text": "Hello!"},
    ]


@override_settings(MANDRILL_API_KEY="mandrill-key")
def test_mandrill_email_payload(httpx_mock):
    httpx_mock.add_response(
        url="https://mandrillapp.com/api/1.0/messages/send",
        json=[{"email": "to@example.org", "status": "sent"}],
    )

    sent = MandrillEmailBackend().send_messages([make_email()])

    assert sent == 1

    request = httpx_mock.get_request()
    payload = json.loads(request.content)

    assert payload["key"] == "mandrill-key"

    message = payload["message"]
    assert message["from_email"] == "sender@example.org"
    assert message["from_name"] == "Sender"
    assert {"email": "to@example.org", "type": "to", "name": "Recipient"} in (
        message["to"]
    )
    assert {"email": "cc@example.org", "type": "cc"} in message["to"]
    assert message["subject"] == "Hi there"
    assert message["text"] == "Text body"
    assert message["html"] == "<p>Html body</p>"
    assert message["headers"] == {"X-Custom": "yes"}


@override_settings(MANDRILL_API_KEY="mandrill-key")
def test_mandrill_email_rejected_counts_zero(httpx_mock):
    httpx_mock.add_response(
        url="https://mandrillapp.com/api/1.0/messages/send",
        json=[{"email": "to@example.org", "status": "rejected"}],
    )

    assert MandrillEmailBackend().send_messages([make_email()]) == 0


@override_settings(**MAILJET_SETTINGS, MAILJET_BASE_URL="https://mj.example.org")
def test_mailjet_base_url_is_configurable(httpx_mock):
    httpx_mock.add_response(
        url="https://mj.example.org/v3.1/send",
        json={"Messages": [{"Status": "success", "To": []}]},
    )

    assert MailjetEmailBackend().send_messages([make_email()]) == 1
