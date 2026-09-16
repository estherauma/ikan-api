from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import TraderVesselOwnerRelationship, User


def make_user(email, group_name=None, **kwargs):
    user = User.objects.create_user(email=email, password='password123', **kwargs)
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


class TraderWebViewsTestCase(TestCase):
    def setUp(self):
        self.admin_group = Group.objects.create(name='admin')
        self.trader_group = Group.objects.create(name='trader')
        self.vessel_owner_group = Group.objects.create(name='vessel_owner')

        self.admin = make_user('admin@example.com', group_name='admin')
        self.trader = make_user(
            'trader@example.com',
            group_name='trader',
            first_name='Tina',
            last_name='Trader',
            is_active=False,
        )
        self.vessel_owner = make_user(
            'owner@example.com',
            group_name='vessel_owner',
            first_name='Vera',
            last_name='Owner',
        )
        self.client.force_login(self.admin)
        session = self.client.session
        session['language'] = 'en'
        session.save()

    def test_trader_list_renders_from_traders_app(self):
        response = self.client.get(reverse('traders:traders'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'traders/list.html')
        self.assertContains(response, self.trader.email)

    def test_trader_detail_renders_from_traders_app(self):
        TraderVesselOwnerRelationship.objects.create(
            trader=self.trader,
            vessel_owner=self.vessel_owner,
            created_by=self.admin.id,
            updated_by=self.admin.id,
        )

        response = self.client.get(reverse('traders:details', kwargs={'pk': self.trader.id}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'traders/detail.html')
        self.assertContains(response, self.vessel_owner.email)

    @patch('traders.views.web.send_user_invite_email', return_value=True)
    def test_invite_trader_creates_inactive_trader_and_returns_json(self, send_invite):
        response = self.client.post(reverse('traders:invite-trader'), {
            'email_or_phone': 'new-trader@example.com',
            'first_name': 'New',
            'last_name': 'Trader',
            'role': 'trader',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        user = User.objects.get(email='new-trader@example.com')
        self.assertFalse(user.is_active)
        self.assertTrue(user.groups.filter(name='trader').exists())
        send_invite.assert_called_once()

    def test_invite_trader_returns_validation_errors(self):
        response = self.client.post(reverse('traders:invite-trader'), {
            'email_or_phone': '',
            'role': 'trader',
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['success'], False)
        self.assertIn('email_or_phone', response.json()['errors'])

    @patch('traders.views.web.send_user_invite_email', return_value=True)
    def test_resend_trader_invite_returns_json_success(self, send_invite):
        response = self.client.post(reverse('traders:resend-invite'), {
            'email': self.trader.email,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        send_invite.assert_called_once_with(self.trader, {})

    def test_attach_vessel_owner_creates_relationship(self):
        response = self.client.post(reverse('traders:details', kwargs={'pk': self.trader.id}), {
            'vessel_owners': [self.vessel_owner.id],
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.assertTrue(
            TraderVesselOwnerRelationship.objects.filter(
                trader=self.trader,
                vessel_owner=self.vessel_owner,
            ).exists()
        )

    def test_remove_vessel_owner_relationship_deletes_relationship(self):
        relationship = TraderVesselOwnerRelationship.objects.create(
            trader=self.trader,
            vessel_owner=self.vessel_owner,
            created_by=self.admin.id,
            updated_by=self.admin.id,
        )

        response = self.client.post(reverse('traders:remove-vessel-owner-relationship', kwargs={
            'pk': self.trader.id,
            'relationship_pk': relationship.id,
        }))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.assertFalse(TraderVesselOwnerRelationship.objects.filter(pk=relationship.pk).exists())
