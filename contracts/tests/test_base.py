from rest_framework.test import APITestCase
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class BaseApiTestCase(APITestCase):
    def setUp(self):
        self.login_url = '/api/v1/auth/login/'

    def login(self, user):
        pass

    def get(self, url, format='json'):
        pass

    def post(self, url, data, format='json'):
        pass

    def put(self, url, data, format='json'):
        pass

    def patch(self, url, data, format='json'):
        pass

    def put(self, url, data, format='json'):
        pass


class BaseTestCase(TestCase):
    def setUp(self):
        # Common setup tasks go here
        # ToDo: Create a test user
        self.assertEqual(1, 1)

    def tearDown(self):
        # Common teardown tasks go here
        pass

    def login(self):
        # Helper method to log in the user
        pass

    def create_test_user(self, username, password):
        # Helper method to create a user
        pass
