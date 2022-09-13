from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """
    The regular Django user with a locale field in addition
    """

    locale = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
    )

    phone_number = PhoneNumberField(
        region="FR",
        blank=True,
        null=True,
    )
