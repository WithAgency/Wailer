import sms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.test import (
    SimpleTestCase,
    TransactionTestCase,
    modify_settings,
    override_settings,
)
from my_app.models import User
from sms.message import Message as SmsMessage

from wailer.backends import parse_email_address
from wailer.errors import WailerTemplateException
from wailer.models import Email, Sms


class TestStaticEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("static", {})

    def get_sent_mail(self) -> EmailMultiAlternatives:
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def test_get_to(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.to, ["foo@bar.com"])

    def test_get_subject(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.subject, "Static Subject")

    def test_rendered_text(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.body, "Static Text en français\n")

    def test_rendered_html(self):
        sent = self.get_sent_mail()
        self.assertEqual(len(sent.alternatives), 1)
        content, mime = sent.alternatives[0]
        self.assertEqual(mime, "text/html")
        self.assertInHTML("Static HTML en français", content, count=1)

    def test_context(self):
        self.assertEqual(self.email.context["prefix"], "Static")


class TestStaticNoTextEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("static-no-text", {})

    def get_sent_mail(self) -> EmailMultiAlternatives:
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def test_has_no_text(self):
        sent = self.get_sent_mail()
        self.assertEqual(len(sent.alternatives), 1)
        self.assertEqual(sent.alternatives[0][1], "text/html")
        self.assertEqual(sent.body, "")


class TestStaticNoHtmlEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("static-no-html", {})

    def get_sent_mail(self) -> EmailMultiAlternatives:
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def test_has_no_html(self):
        sent = self.get_sent_mail()
        self.assertEqual(len(sent.alternatives), 0)
        self.assertNotEqual(sent.body, "")


class TestHello(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send(
            "hello",
            dict(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.org",
                locale="fr",
            ),
        )

    def get_sent_mail(self) -> EmailMultiAlternatives:
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def test_get_subject(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.subject, "Salut John Doe")

    def test_get_to(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.to, ["john.doe@example.org"])

    def test_rendered_text(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.body, "Salut John Doe!\n\nÀ plus la pluche\n")

    def test_rendered_html(self):
        sent = self.get_sent_mail()
        self.assertEqual(len(sent.alternatives), 1)
        content, mime = sent.alternatives[0]
        self.assertEqual(mime, "text/html")
        self.assertInHTML("Bonjour, John Doe!", content, count=1)


class TestHelloUser(TransactionTestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="test",
            email="john.doe@example.org",
            first_name="John",
            last_name="Doe",
            locale="fr",
        )
        self.email = Email.send("hello-user", dict(user_id=self.user.id), self.user)

    def get_sent_mail(self) -> EmailMultiAlternatives:
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def test_get_subject(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.subject, "Salut John Doe")

    def test_get_to(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.to, ["john.doe@example.org"])

    def test_rendered_text(self):
        sent = self.get_sent_mail()
        self.assertEqual(sent.body, "Salut John Doe!\n\nÀ plus la pluche\n")

    def test_after_user_change(self):
        self.user.first_name = "Jack"
        self.user.save()

        self.email.send_now()
        sent = mail.outbox[-1]

        self.assertEqual(sent.subject, "Salut John Doe")

    def test_delete_after_user(self):
        self.assertTrue(Email.objects.filter(pk=self.email.pk).exists())
        self.user.delete()
        self.assertFalse(Email.objects.filter(pk=self.email.pk).exists())

    def test_rendered_html(self):
        sent = self.get_sent_mail()
        self.assertEqual(len(sent.alternatives), 1)
        content, mime = sent.alternatives[0]
        self.assertEqual(mime, "text/html")
        self.assertInHTML("Bonjour, John Doe!", content, count=1)


class TestStyledEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("styled-html", {})

    def get_sent_mail(self) -> EmailMultiAlternatives:
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def test_h1_has_style(self):
        sent = self.get_sent_mail()
        content, _ = sent.alternatives[0]
        self.assertInHTML('<h1 style="color:red">Hello</h1>', content)


class TestGetBaseUrl(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("styled-html", {})

    @override_settings(WAILER_BASE_URL="https://example.org")
    def test_wailer_base_url(self):
        self.assertEqual(self.email.email.get_base_url(), "https://example.org")

    @override_settings(WAILER_SITE_ID=1)
    def test_wailer_site_id(self):
        site = Site.objects.get(pk=1)
        site.domain = "example.org"
        site.save()

        self.assertEqual(self.email.email.get_base_url(), "https://example.org")

    def test_default_site_example(self):
        site = Site.objects.get(pk=1)
        site.domain = "example.org"
        site.save()

        self.assertEqual(self.email.email.get_base_url(), "https://example.org")

    def test_default_site_localhost(self):
        site = Site.objects.get(pk=1)
        site.domain = "localhost:8000"
        site.save()

        self.assertEqual(self.email.email.get_base_url(), "http://localhost:8000")

    def test_default_site_local_ip(self):
        site = Site.objects.get(pk=1)
        site.domain = "127.0.0.1:8000"
        site.save()

        self.assertEqual(self.email.email.get_base_url(), "http://127.0.0.1:8000")

    @modify_settings(INSTALLED_APPS=dict(remove=["django.contrib.sites"]))
    def test_no_guess(self):
        with self.assertRaises(WailerTemplateException):
            self.email.email.get_base_url()


class TestEmailPermalink(TransactionTestCase):
    def setUp(self) -> None:
        site = Site.objects.get(pk=1)
        site.domain = "wailer.org"
        site.save()

        self.user = User.objects.create_user(
            username="test",
            email="john.doe@example.org",
            first_name="John",
            last_name="Doe",
            locale="fr",
        )
        self.email = Email.send("hello-user", dict(user_id=self.user.id), self.user)

    def test_get_txt(self):
        response = self.client.get(self.email.link_text)
        self.assertEqual(response.context["self"], self.email)
        self.assertEqual(response.resolver_match.kwargs["email_uuid"], self.email.pk)
        self.assertEqual(
            response.content.decode(response.charset),
            "Salut John Doe!\n\nÀ plus la pluche\n",
        )

    def test_get_html(self):
        response = self.client.get(self.email.link_html)
        self.assertEqual(response.context["self"], self.email)
        self.assertEqual(response.resolver_match.kwargs["email_uuid"], self.email.pk)
        self.assertInHTML(
            "Bonjour, John Doe!",
            response.content.decode(response.charset),
            count=1,
        )

    def test_get_invalid_format(self):
        response = self.client.get(self.email.link_text.replace(".txt", ".nope"))
        self.assertEqual(response.status_code, 404)

    def get_sent_mail(self) -> EmailMultiAlternatives:
        self.assertEqual(len(mail.outbox), 1)
        return mail.outbox[0]

    def test_permalink_in_mail(self):
        sent = self.get_sent_mail()
        content, _ = sent.alternatives[0]
        self.assertInHTML(
            f"""
                <a href="https://wailer.org/wailer/email/{self.email.pk}.html">
                    Click here to display this email in a browser
                </a>
            """,
            content,
        )


class TestAbsoluteUrl(TransactionTestCase):
    def setUp(self) -> None:
        site = Site.objects.get(pk=1)
        site.domain = "wailer.org"
        site.save()

    def test_straight(self):
        email = Email.send("absolute-url-straight", {})
        self.assertEqual(email.email.get_text_content(), "https://wailer.org/\n")

    def test_as(self):
        email = Email.send("absolute-url-as", {})
        self.assertEqual(
            email.email.get_text_content(),
            "1 = , 2 = https://wailer.org/\n",
        )

    def test_make_absolute(self):
        email = Email.send("make-absolute", {})
        self.assertEqual(email.email.get_text_content(), "https://wailer.org/foo/bar\n")


class TestMailjetEmailBackend(SimpleTestCase):
    def test_parse_email_address(self):
        self.assertEqual(parse_email_address("foo@bar.com"), dict(Email="foo@bar.com"))
        self.assertEqual(
            parse_email_address("Foo <foo@bar.com>"),
            dict(Email="foo@bar.com", Name="Foo"),
        )

        with self.assertRaisesMessage(ValueError, "Invalid e-mail format: <<<"):
            parse_email_address("<<<")


class TestSendSms(TransactionTestCase):
    def setUp(self) -> None:
        self.sms = Sms.send("hello", {"word": "Foo"})

    def test_locmem_backend(self):
        self.assertEqual(settings.SMS_BACKEND, "sms.backends.locmem.SmsBackend")

    def get_sent_sms(self) -> SmsMessage:
        self.assertEqual(len(sms.outbox), 1)  # noqa
        return sms.outbox[0]  # noqa

    def test_get_to(self):
        sent = self.get_sent_sms()
        self.assertEqual(sent.recipients, ["+34659424242"])

    def test_rendered_text(self):
        sent = self.get_sent_sms()
        self.assertEqual(sent.body, "Bonjour Foo\xa0!")

    def test_context(self):
        self.assertEqual(self.sms.context["word"], "Foo")
