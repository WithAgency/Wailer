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
