"""Django app configuration for Wailer."""

from functools import wraps

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


def monkey_patch_sms_into_unit_tests():
    """
    Django's test runner will take care to change some essential settings to
    make testing easier, including having a memory-only email backend. That's
    definitely a behavior we also want to have for SMS sending as well.

    Good news and bad news: there are no official way to hook on test runner
    initialization, but you can always monkey patch and do the same thing for
    SMSes as what is done for emails.

    So basically this is fairly dirty code that will need to be maintained from
    one version of Django to the other one. However, since it's going to break
    the tests if Django breaks this internal interface, we'll notice it
    quickly I guess.

    🐒🐒🐒
    """

    from django.test import SimpleTestCase, utils

    original_global = utils.setup_test_environment

    if getattr(original_global, "_wailer_sms", False):
        return
    else:
        original_global._wailer_sms = True

    @wraps(original_global)
    def patched_pre(*args, **kwargs):
        import sms
        from django.conf import settings

        original_global(*args, **kwargs)

        settings.SMS_BACKEND = "sms.backends.locmem.SmsBackend"

        if not hasattr(sms, "outbox"):
            sms.outbox = []

    utils.setup_test_environment = patched_pre

    # In Django < 6.1 _pre_setup is an instance method while starting from
    # 6.1 it is a classmethod, so we need to look at the raw attribute to
    # know how to re-wrap it after patching.
    raw_local = SimpleTestCase.__dict__["_pre_setup"]
    is_classmethod = isinstance(raw_local, classmethod)
    original_local = raw_local.__func__ if is_classmethod else raw_local

    @wraps(original_local)
    def patched_local(*args, **kwargs):
        import sms

        original_local(*args, **kwargs)
        sms.outbox = []

    SimpleTestCase._pre_setup = (
        classmethod(patched_local) if is_classmethod else patched_local
    )


class WailerConfig(AppConfig):
    """
    Giving some meta-info about Wailer
    """

    name = "wailer"
    verbose_name = _("Wailer")

    def ready(self):
        """
        When the app inits we use this opportunity to monkey-patch the tests
        runner.
        """

        monkey_patch_sms_into_unit_tests()
