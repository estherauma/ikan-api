from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APITestCase
from faker import Faker


class BaseTestCase(APITestCase):
    def set_up(self):
        pass

    def create_user(self):
        pass

    def login(self):
        pass

    def tests_first(self):
        self.assertEqual(200, 200)

    def test_login_url_exits(self):
        pass

    def test_logout_url_exists(self):
        self.assertEqual(1,2)
