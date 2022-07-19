from django.urls import reverse
from django.test import TestCase

class BaseTestCase(TestCase):
    def tests_first(self):
        self.assertEqual(200, 200)
