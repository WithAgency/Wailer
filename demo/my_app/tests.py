import pytest
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
from django.utils.encoding import force_bytes
from sms.message import Message as SmsMessage

from my_app.models import User
from wailer.backends.mailjet import parse_email_address
from wailer.errors import WailerTemplateException
from wailer.models import Email, Sms


class TestStaticEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("static", {})

    def get_sent_mail(self) -> EmailMultiAlternatives:
        assert len(mail.outbox) == 1
        return mail.outbox[0]

    def test_get_to(self):
        sent = self.get_sent_mail()
        assert sent.to == ["foo@bar.com"]

    def test_get_subject(self):
        sent = self.get_sent_mail()
        assert sent.subject == "Static Subject"

    def test_rendered_text(self):
        sent = self.get_sent_mail()
        assert sent.body == "Static Text en français\n"

    def test_rendered_html(self):
        sent = self.get_sent_mail()
        assert len(sent.alternatives) == 1
        content, mime = sent.alternatives[0]
        assert mime == "text/html"
        self.assertInHTML("Static HTML en français", content, count=1)

    def test_context(self):
        assert self.email.context["prefix"] == "Static"


class TestStaticNoTextEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("static-no-text", {})

    def get_sent_mail(self) -> EmailMultiAlternatives:
        assert len(mail.outbox) == 1
        return mail.outbox[0]

    def test_has_no_text(self):
        sent = self.get_sent_mail()
        assert len(sent.alternatives) == 1
        assert sent.alternatives[0][1] == "text/html"
        assert sent.body == ""


class TestStaticNoHtmlEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("static-no-html", {})

    def get_sent_mail(self) -> EmailMultiAlternatives:
        assert len(mail.outbox) == 1
        return mail.outbox[0]

    def test_has_no_html(self):
        sent = self.get_sent_mail()
        assert len(sent.alternatives) == 0
        assert sent.body != ""


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
        assert len(mail.outbox) == 1
        return mail.outbox[0]

    def test_get_subject(self):
        sent = self.get_sent_mail()
        assert sent.subject == "Salut John Doe"

    def test_get_to(self):
        sent = self.get_sent_mail()
        assert sent.to == ["john.doe@example.org"]

    def test_rendered_text(self):
        sent = self.get_sent_mail()
        assert sent.body == "Salut John Doe!\n\nÀ plus la pluche\n"

    def test_rendered_html(self):
        sent = self.get_sent_mail()
        assert len(sent.alternatives) == 1
        content, mime = sent.alternatives[0]
        assert mime == "text/html"
        self.assertInHTML("Bonjour, John Doe!", content, count=1)


class TestHelloMjml(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send(
            "hello-mjml",
            dict(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.org",
                locale="fr",
            ),
        )

    def get_sent_mail(self) -> EmailMultiAlternatives:
        assert len(mail.outbox) == 1
        return mail.outbox[0]

    def test_rendered_html(self):
        sent = self.get_sent_mail()
        assert len(sent.alternatives) == 1
        content, mime = sent.alternatives[0]
        assert mime == "text/html"
        self.assertInHTML("Bonjour, John Doe!", content, count=1)


class TestHelloAttachment(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send(
            "hello-attachment",
            dict(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.org",
                locale="fr",
            ),
        )

    def get_sent_mail(self) -> EmailMultiAlternatives:
        assert len(mail.outbox) == 1
        return mail.outbox[0]

    def test_attachment(self):
        sent = self.get_sent_mail()
        assert len(sent.attachments) == 1
        filename, content, mimetype = sent.attachments[0]
        assert filename == "hello.txt"
        assert force_bytes(content) == b"\x00\x01\x02"
        assert mimetype == "application/octet-stream"


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
        assert len(mail.outbox) == 1
        return mail.outbox[0]

    def test_get_subject(self):
        sent = self.get_sent_mail()
        assert sent.subject == "Salut John Doe"

    def test_get_to(self):
        sent = self.get_sent_mail()
        assert sent.to == ["john.doe@example.org"]

    def test_rendered_text(self):
        sent = self.get_sent_mail()
        assert sent.body == "Salut John Doe!\n\nÀ plus la pluche\n"

    def test_after_user_change(self):
        self.user.first_name = "Jack"
        self.user.save()

        self.email.send_now()
        sent = mail.outbox[-1]

        assert sent.subject == "Salut John Doe"

    def test_delete_after_user(self):
        assert Email.objects.filter(pk=self.email.pk).exists()
        self.user.delete()
        assert not Email.objects.filter(pk=self.email.pk).exists()

    def test_rendered_html(self):
        sent = self.get_sent_mail()
        assert len(sent.alternatives) == 1
        content, mime = sent.alternatives[0]
        assert mime == "text/html"
        self.assertInHTML("Bonjour, John Doe!", content, count=1)


class TestStyledEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("styled-html", {})

    def get_sent_mail(self) -> EmailMultiAlternatives:
        assert len(mail.outbox) == 1
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
        assert self.email.email.get_base_url() == "https://example.org"

    @override_settings(BASE_URL="https://base.example.org")
    def test_base_url(self):
        assert self.email.email.get_base_url() == "https://base.example.org"

    @override_settings(
        WAILER_BASE_URL="https://wailer.example.org",
        BASE_URL="https://base.example.org",
    )
    def test_wailer_base_url_wins_over_base_url(self):
        assert self.email.email.get_base_url() == "https://wailer.example.org"

    @override_settings(WAILER_SITE_ID=1)
    def test_wailer_site_id(self):
        site = Site.objects.get(pk=1)
        site.domain = "example.org"
        site.save()

        assert self.email.email.get_base_url() == "https://example.org"

    def test_default_site_example(self):
        site = Site.objects.get(pk=1)
        site.domain = "example.org"
        site.save()

        assert self.email.email.get_base_url() == "https://example.org"

    def test_default_site_localhost(self):
        site = Site.objects.get(pk=1)
        site.domain = "localhost:8000"
        site.save()

        assert self.email.email.get_base_url() == "http://localhost:8000"

    def test_default_site_local_ip(self):
        site = Site.objects.get(pk=1)
        site.domain = "127.0.0.1:8000"
        site.save()

        assert self.email.email.get_base_url() == "http://127.0.0.1:8000"

    @modify_settings(INSTALLED_APPS=dict(remove=["django.contrib.sites"]))
    def test_no_guess(self):
        with pytest.raises(WailerTemplateException):
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
        assert response.context["self"] == self.email
        assert response.resolver_match.kwargs["email_uuid"] == self.email.pk
        expected = "Salut John Doe!\n\nÀ plus la pluche\n"
        assert response.content.decode(response.charset) == expected

    def test_get_html(self):
        response = self.client.get(self.email.link_html)
        assert response.context["self"] == self.email
        assert response.resolver_match.kwargs["email_uuid"] == self.email.pk
        self.assertInHTML(
            "Bonjour, John Doe!",
            response.content.decode(response.charset),
            count=1,
        )

    def test_get_invalid_format(self):
        response = self.client.get(self.email.link_text.replace(".txt", ".nope"))
        assert response.status_code == 404

    def get_sent_mail(self) -> EmailMultiAlternatives:
        assert len(mail.outbox) == 1
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
        assert email.email.get_text_content() == "https://wailer.org/\n"

    def test_as(self):
        email = Email.send("absolute-url-as", {})
        assert email.email.get_text_content() == "1 = , 2 = https://wailer.org/\n"

    def test_make_absolute(self):
        email = Email.send("make-absolute", {})
        assert email.email.get_text_content() == "https://wailer.org/foo/bar\n"


class TestMailjetEmailBackend(SimpleTestCase):
    def test_parse_email_address(self):
        assert parse_email_address("foo@bar.com") == dict(Email="foo@bar.com")
        expected = dict(Email="foo@bar.com", Name="Foo")
        assert parse_email_address("Foo <foo@bar.com>") == expected

        with self.assertRaisesMessage(ValueError, "Invalid e-mail format: <<<"):
            parse_email_address("<<<")


class TestSendSms(TransactionTestCase):
    def setUp(self) -> None:
        self.sms = Sms.send("hello", {"word": "Foo"})

    def test_locmem_backend(self):
        assert settings.SMS_BACKEND == "sms.backends.locmem.SmsBackend"

    def get_sent_sms(self) -> SmsMessage:
        self.assertEqual(len(sms.outbox), 1)  # noqa
        return sms.outbox[0]

    def test_get_to(self):
        sent = self.get_sent_sms()
        assert sent.recipients == ["+34659424242"]

    def test_rendered_text(self):
        sent = self.get_sent_sms()
        assert sent.body == "Bonjour Foo\xa0!"

    def test_context(self):
        assert self.sms.context["word"] == "Foo"


class TestHelloUserSms(TransactionTestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="test",
            email="john.doe@example.org",
            first_name="John",
            last_name="Doe",
            locale="fr",
            phone_number="+34659424242",
        )
        self.sms = Sms.send("hello-user", dict(user_id=self.user.id), self.user)

    def get_sent_sms(self) -> SmsMessage:
        self.assertEqual(len(sms.outbox), 1)  # noqa
        return sms.outbox[0]

    def test_body(self):
        sent = self.get_sent_sms()
        assert sent.body == "Salut John Doe"

    def test_get_to(self):
        sent = self.get_sent_sms()
        assert sent.recipients == ["+34659424242"]

    def test_after_user_change(self):
        self.user.first_name = "Jack"
        self.user.save()

        self.sms.send_now()
        sent = sms.outbox[-1]

        assert sent.body == "Salut John Doe"

    def test_delete_after_user(self):
        assert Sms.objects.filter(pk=self.sms.pk).exists()
        self.user.delete()
        assert not Sms.objects.filter(pk=self.sms.pk).exists()


class TestComeHomeUserSms(TransactionTestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="test",
            email="john.doe@example.org",
            first_name="John",
            last_name="Doe",
            locale="fr",
            phone_number="+34659424242",
        )
        self.sms = Sms.send("come-home", dict(user_id=self.user.id), self.user)

    def get_sent_sms(self) -> SmsMessage:
        self.assertEqual(len(sms.outbox), 1)  # noqa
        return sms.outbox[0]

    def test_body(self):
        sent = self.get_sent_sms()
        assert (
            sent.body == "Salut John Doe, viens à la maison ici : https://example.com/"
        )
