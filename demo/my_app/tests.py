from django.core import mail
from django.core.mail import EmailMessage
from django.test import TransactionTestCase
from my_app.models import User

from wailer.models import Email


class TestStaticEmail(TransactionTestCase):
    def setUp(self) -> None:
        self.email = Email.send("static", {})

    def get_sent_mail(self) -> EmailMessage:
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

    def test_context(self):
        self.assertEqual(self.email.context["prefix"], "Static")


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

    def get_sent_mail(self) -> EmailMessage:
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

    def get_sent_mail(self) -> EmailMessage:
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
