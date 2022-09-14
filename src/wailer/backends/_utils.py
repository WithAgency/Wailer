from typing import Mapping, Union

from django.core.mail import EmailMessage, EmailMultiAlternatives


def by_alternatives(
    message: Union[EmailMultiAlternatives, EmailMessage],
) -> Mapping[str, str]:
    """
    Flattens all alternatives of this email in order to receive them indexed
    by mime type.

    Parameters
    ----------
    message
        An email message
    """

    def list_all():
        if message.body:
            yield f"text/{message.content_subtype}", message.body

        if isinstance(message, EmailMultiAlternatives):
            for alt, mime in message.alternatives:
                yield mime, alt

    return dict(list_all())
