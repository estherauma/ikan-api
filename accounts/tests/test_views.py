from datetime import timedelta
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User


def make_user(email, **kwargs):
    return User.objects.create_user(email=email, password='password123', **kwargs)


class AccountSetupViewTestCase(TestCase):
    @patch('accounts.views.web.ContentUtils')
    def test_expired_invite_link_shows_error_on_submit(self, content_utils):
        content_utils.return_value.get_page_text.return_value = {}
        user = make_user('expired@example.com', is_active=False)
        user.reset_password_token = 'expired-token'
        user.reset_password_token_created_at = timezone.now() - timedelta(days=3, seconds=1)
        user.save()

        response = self.client.post(reverse('accounts:setup-account'), {
            'email': user.email,
            'token': user.reset_password_token,
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })

        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['invalid_link'])
        self.assertIn('This account setup link is invalid or has expired.', messages)
