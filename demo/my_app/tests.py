from django.test import TransactionTestCase


class TestTester(TransactionTestCase):
    def test_nothing(self):
        self.assertTrue(True)
