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
        pass

    def test_login_url_exits(self):
        pass

    def test_logout_url_exists(self):
        pass

    def test_camel_to_snake_case_coversion(self):
        response = self.client.get(reverse('sample'))
        result = response.json()
        self.assertIn('testData', result)
        

    def test_snake_to_camel_case_conversion(self):
        response = self.client.post(reverse('sample'),  {
            "parserWorks": "Parser workers"
        })
        result = response.json()
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'OK')
