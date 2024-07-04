from django.urls import reverse
from rest_framework.test import APITestCase
from faker import Faker


class BaseTestCase(APITestCase):
    def set_up(self):
        self.faker = Faker()

    def create_user(self):
        pass

    def login(self):
        pass

    def post(self, url, data, format='json'):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {token}'.format(token=self.token))
        response = self.client.post(url, data, format=format)
        return response

    def get(self, url, auth=True):
        '''Makes a GET request'''
        if auth:
            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer {token}'.format(token=self.token))
        response = self.client.get(url)
        return response

    def put(self, url):
        '''Makes a PUT request'''
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {token}'.format(token=self.token))
        response = self.client.put(url)
        return response

    def patch(self, url, data):
        '''Makes a PATCH request'''
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {token}'.format(token=self.token))
        response = self.client.patch(url, data)
        return response

    def delete(self, url):
        '''Makes a DELETE request'''
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {token}'.format(token=self.token))
        response = self.client.delete(url)
        return response

    def test_camel_to_snake_case_coversion(self):
        response = self.client.get(reverse('sample'))
        result = response.json()
        self.assertIn('testData', result)

    def test_snake_to_camel_case_conversion(self):
        response = self.client.post(reverse('sample'), {
            "parserWorks": "Parser workers"
        })
        result = response.json()
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'OK')
