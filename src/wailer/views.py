from typing import Text
from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from .models import Email, Sms


def email(request: HttpRequest, email_uuid: UUID, fmt: Text) -> HttpResponse:
    """
    Renders an email in the requested format

    Parameters
    ----------
    request
        HTTP request
    email_uuid
        UUID of the email
    fmt
        Display format (txt or html)
    """

    q = get_object_or_404(Email, pk=email_uuid)

    if fmt == "html":
        return HttpResponse(q.email.get_html_content())
    elif fmt == "txt":
        return HttpResponse(q.email.get_text_content(), content_type="plain/text")
    else:
        raise NotImplementedError


def sms(request: HttpRequest, sms_uuid: UUID) -> HttpResponse:
    """
    Renders a SMS

    Parameters
    ----------
    request
        HTTP request
    sms_uuid
        UUID of the sms
    """

    q = get_object_or_404(Sms, pk=sms_uuid)

    return HttpResponse(q.sms.get_content(), content_type="plain/text")


def pixel(request: HttpRequest, email_uuid: UUID) -> HttpResponse:
    """
    Adds an open for the email and tracks the user agent.

    :param request: Django request
    :param email_uuid: email's UUID
    """

    e = get_object_or_404(Email, uuid=email_uuid)

    ua = request.META.get("HTTP_USER_AGENT", "")

    if len(ua) > Open.AGENT_MAX_LENGTH:
        return HttpResponse(b"", status=413)

    Open.objects.create(email=e, agent=ua)

    g = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9"
        b"\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
        b"\x01D\x00;"
    )
    return HttpResponse(g, content_type="image/gif")
