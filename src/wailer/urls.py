"""URL patterns to view sent emails and SMSes in a browser."""

from django.urls import path, register_converter

from .views import email, sms


class EmailFormatConverter:
    """
    Detects an email format extension
    """

    regex = "(txt|html)"

    def to_python(self, value):
        """Return the matched format as-is."""
        return value

    def to_url(self, value):
        """Return the format as-is for URL generation."""
        return value


register_converter(EmailFormatConverter, "email_format")


urlpatterns = [
    path("email/<uuid:email_uuid>.<email_format:fmt>", email, name="view_email"),
    path("sms/<uuid:sms_uuid>", sms, name="view_sms"),
]
