from django.test import TestCase
from accounts.models import User
from faker import Faker


class AuthModelTestCase(TestCase):

    def setUp(self) -> None:
        self.faker = Faker()

    def test_can_create_user(self):
        user = User.objects.create_user(
            password=self.faker.password(),
            email=self.faker.email()
        )
        self.assertIsNotNone(user)
        self.assertIsNotNone(user.id)
