from collections import defaultdict
from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import TraderVesselOwnerRelationship, User
from vessels.models import Vessel
from wages.models import Wage


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

    @patch('common.services.translation.PrismicUtils')
    def test_trader_detail_renders_from_traders_app(self, prismic_utils):
        common_text = defaultdict(str)
        common_text.update({
            'view': 'View',
        })
        prismic_utils.return_value.get_common_text.return_value = common_text
        prismic_utils.return_value.get_page_text.return_value = defaultdict(str)
        prismic_utils.return_value.get_form_questions.return_value = []

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


class TraderDashboardWagePaymentsViewTestCase(TestCase):
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
            is_active=True,
        )
        self.vessel_owner = make_user(
            'owner@example.com',
            group_name='vessel_owner',
            first_name='Vera',
            last_name='Owner',
        )
        self.crew_member = make_user(
            'crew@example.com',
            group_name='crew',
            first_name='Carl',
            last_name='Crew',
        )

        # Create a vessel
        self.vessel = Vessel.objects.create(
            name='Test Vessel',
            created_by=self.vessel_owner.id,
            updated_by=self.vessel_owner.id,
        )

        # Create trader-vessel owner relationship
        self.relationship = TraderVesselOwnerRelationship.objects.create(
            trader=self.trader,
            vessel_owner=self.vessel_owner,
            created_by=self.admin.id,
            updated_by=self.admin.id,
        )

        session = self.client.session
        session['language'] = 'en'
        session.save()

    def configure_prismic_mock(self, prismic_utils, page_text):
        prismic_utils.return_value.get_page_text.return_value = page_text
        prismic_utils.return_value.get_common_text.return_value = {}
        prismic_utils.return_value.get_form_questions.return_value = []

    def test_wage_payments_view_requires_login(self):
        response = self.client.get(reverse('traders:dashboard-wage-payments'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    def test_wage_payments_view_requires_trader_role(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))
        self.assertEqual(response.status_code, 403)

    @patch('common.services.translation.PrismicUtils')
    def test_wage_payments_view_renders_for_trader(self, prismic_utils):
        dashboard_text = defaultdict(str)
        dashboard_text.update({
            'wagePayments': 'Wage Payments',
            'overview': 'Overview',
            'status': 'Status',
            'all': 'All',
            'noIssues': 'No Issues',
            'nonCompliant': 'Non-Compliant',
            'suppliersVesselOwners': 'Suppliers / Vessel Owners',
            'payslips': 'Payslips',
        })
        self.configure_prismic_mock(prismic_utils, dashboard_text)

        self.client.force_login(self.trader)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'traders/dashboard/wage_payments.html')

    @patch('common.services.translation.PrismicUtils')
    def test_wage_payments_view_context_contains_required_keys(self, prismic_utils):
        dashboard_text = defaultdict(str)
        dashboard_text.update({
            'wagePayments': 'Wage Payments',
            'overview': 'Overview',
            'status': 'Status',
            'all': 'All',
            'noIssues': 'No Issues',
            'nonCompliant': 'Non-Compliant',
            'suppliersVesselOwners': 'Suppliers / Vessel Owners',
            'payslips': 'Payslips',
            'filterBasedOn': 'Filter Based On',
        })
        self.configure_prismic_mock(prismic_utils, dashboard_text)

        self.client.force_login(self.trader)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))

        context = response.context
        self.assertIn('payment_summary', context)
        self.assertIn('supplier_filters', context)
        self.assertIn('status_filter_options', context)
        self.assertIn('supplier_rows', context)

    @patch('common.services.translation.PrismicUtils')
    def test_wage_payments_view_status_filter_options(self, prismic_utils):
        dashboard_text = defaultdict(str)
        dashboard_text.update({
            'wagePayments': 'Wage Payments',
            'overview': 'Overview',
            'status': 'Status',
            'all': 'All',
            'noIssues': 'No Issues',
            'nonCompliant': 'Non-Compliant',
        })
        self.configure_prismic_mock(prismic_utils, dashboard_text)

        self.client.force_login(self.trader)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))

        filter_options = response.context['status_filter_options']
        self.assertEqual(len(filter_options), 3)
        self.assertEqual(filter_options[0]['value'], 'all')
        self.assertEqual(filter_options[1]['value'], 'no_issues')
        self.assertEqual(filter_options[2]['value'], 'non_compliant')

    @patch('common.services.translation.PrismicUtils')
    def test_wage_payments_view_supplier_status_no_issues(self, prismic_utils):
        dashboard_text = defaultdict(str)
        dashboard_text.update({
            'wagePayments': 'Wage Payments',
            'overview': 'Overview',
            'status': 'Status',
            'all': 'All',
            'noIssues': 'No Issues',
            'nonCompliant': 'Non-Compliant',
            'suppliersVesselOwners': 'Suppliers / Vessel Owners',
            'payslips': 'Payslips',
            'filterBasedOn': 'Filter Based On',
            'crew': 'crew',
            'noVessels': 'No Vessels',
        })
        self.configure_prismic_mock(prismic_utils, dashboard_text)

        # Create a wage with received status
        wage = Wage.objects.create(
            vessel=self.vessel,
            user=self.crew_member,
            payment_date=date.today(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            usd_amount=500.00,
            status='received',
        )

        self.client.force_login(self.trader)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))

        supplier_rows = response.context['supplier_rows']
        self.assertEqual(supplier_rows[0]['status_value'], 'no_issues')
        self.assertEqual(supplier_rows[0]['status_class'], 'good')

    @patch('common.services.translation.PrismicUtils')
    def test_wage_payments_view_supplier_status_non_compliant(self, prismic_utils):
        dashboard_text = defaultdict(str)
        dashboard_text.update({
            'wagePayments': 'Wage Payments',
            'overview': 'Overview',
            'status': 'Status',
            'all': 'All',
            'noIssues': 'No Issues',
            'nonCompliant': 'Non-Compliant',
            'suppliersVesselOwners': 'Suppliers / Vessel Owners',
            'payslips': 'Payslips',
            'filterBasedOn': 'Filter Based On',
            'crew': 'crew',
            'noVessels': 'No Vessels',
        })
        self.configure_prismic_mock(prismic_utils, dashboard_text)

        # Create a wage with issue_pending status
        wage = Wage.objects.create(
            vessel=self.vessel,
            user=self.crew_member,
            payment_date=date.today(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            usd_amount=500.00,
            status='issue_pending',
        )

        self.client.force_login(self.trader)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))

        supplier_rows = response.context['supplier_rows']
        self.assertEqual(supplier_rows[0]['status_value'], 'non_compliant')
        self.assertEqual(supplier_rows[0]['status_class'], 'danger')

    @patch('common.services.translation.PrismicUtils')
    def test_wage_payments_view_multiple_suppliers(self, prismic_utils):
        dashboard_text = defaultdict(str)
        dashboard_text.update({
            'wagePayments': 'Wage Payments',
            'overview': 'Overview',
            'status': 'Status',
            'all': 'All',
            'noIssues': 'No Issues',
            'nonCompliant': 'Non-Compliant',
            'suppliersVesselOwners': 'Suppliers / Vessel Owners',
            'payslips': 'Payslips',
            'filterBasedOn': 'Filter Based On',
            'crew': 'crew',
            'noVessels': 'No Vessels',
        })
        self.configure_prismic_mock(prismic_utils, dashboard_text)

        # Create a second vessel owner and relationship
        vessel_owner_2 = make_user(
            'owner2@example.com',
            group_name='vessel_owner',
            first_name='Victor',
            last_name='Owner2',
        )
        vessel_2 = Vessel.objects.create(
            name='Test Vessel 2',
            created_by=vessel_owner_2.id,
            updated_by=vessel_owner_2.id,
        )
        TraderVesselOwnerRelationship.objects.create(
            trader=self.trader,
            vessel_owner=vessel_owner_2,
            created_by=self.admin.id,
            updated_by=self.admin.id,
        )

        # Create wages for both suppliers
        wage_1 = Wage.objects.create(
            vessel=self.vessel,
            user=self.crew_member,
            payment_date=date.today(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            usd_amount=500.00,
            status='received',
        )
        wage_2 = Wage.objects.create(
            vessel=vessel_2,
            user=self.crew_member,
            payment_date=date.today(),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            usd_amount=600.00,
            status='issue_pending',
        )

        self.client.force_login(self.trader)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))

        supplier_rows = response.context['supplier_rows']
        self.assertEqual(len(supplier_rows), 2)
        self.assertEqual(supplier_rows[0]['name'], 'Vera Owner')
        self.assertEqual(supplier_rows[0]['payslip_count'], 1)
        self.assertEqual(supplier_rows[1]['name'], 'Victor Owner2')
        self.assertEqual(supplier_rows[1]['payslip_count'], 1)

    @patch('common.services.translation.PrismicUtils')
    def test_wage_payments_view_no_suppliers(self, prismic_utils):
        """Test view when trader has no vessel owner relationships."""
        dashboard_text = defaultdict(str)
        dashboard_text.update({
            'wagePayments': 'Wage Payments',
            'overview': 'Overview',
            'status': 'Status',
            'all': 'All',
            'noIssues': 'No Issues',
            'nonCompliant': 'Non-Compliant',
            'suppliersVesselOwners': 'Suppliers / Vessel Owners',
            'payslips': 'Payslips',
            'filterBasedOn': 'Filter Based On',
        })
        self.configure_prismic_mock(prismic_utils, dashboard_text)

        # Create a new trader with no relationships
        new_trader = make_user(
            'trader2@example.com',
            group_name='trader',
            first_name='Tina2',
            last_name='Trader2',
            is_active=True,
        )

        self.client.force_login(new_trader)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))

        supplier_rows = response.context['supplier_rows']
        self.assertEqual(len(supplier_rows), 0)

    @patch('common.services.translation.PrismicUtils')
    def test_wage_payments_view_payment_summary_structure(self, prismic_utils):
        dashboard_text = defaultdict(str)
        dashboard_text.update({
            'wagePayments': 'Wage Payments',
            'overview': 'Overview',
            'status': 'Status',
            'all': 'All',
            'noIssues': 'No Issues',
            'nonCompliant': 'Non-Compliant',
            'suppliersVesselOwners': 'Suppliers / Vessel Owners',
            'payslips': 'Payslips',
            'filterBasedOn': 'Filter Based On',
            'totalPaymentCompletion': 'Total Payment Completion',
            'completed': 'Completed',
            'payslipStatus': 'Payslip Status',
            'crew': 'crew',
            'noVessels': 'No Vessels',
        })
        self.configure_prismic_mock(prismic_utils, dashboard_text)

        self.client.force_login(self.trader)
        response = self.client.get(reverse('traders:dashboard-wage-payments'))

        payment_summary = response.context['payment_summary']
        self.assertIn('completion', payment_summary)
        self.assertIn('metric_groups', payment_summary)
        self.assertIn('title', payment_summary['completion'])
        self.assertIn('chart_segments', payment_summary['completion'])
        self.assertIn('legend', payment_summary['completion'])
