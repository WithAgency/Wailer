from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    The regular Django user with a locale field in addition
    """

    locale = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
    )
