from django.test import TestCase
from faker import Faker


class ContractModelTestCase(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()

    def test_can_create_contract(self):
        self.assertEqual(1, 1)


class ContractViewTestCase(TestCase):
    def setUp(self) -> None:
        self.faker = Faker()

    def test_can_get_all_contracts(self):
        self.assertEqual(1, 1)
