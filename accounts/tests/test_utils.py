from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase

from accounts.models import AgentVesselOwnerRelationship, User
from accounts.utils import get_sync_data
from companies.models import Company
from contracts.models import Contract, ContractClause, UserContractAccess
from vessels.models import Vessel
from wages.models import Wage


def make_user(email, group_name=None, **kwargs):
    user = User.objects.create_user(email=email, password='password123', **kwargs)
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)
    return user


def make_contract_with_vessel(vessel, name='contract'):
    contract = Contract.objects.create(
        name=name, app_ref=name, start_date=date(2024, 1, 1), end_date=date(2024, 12, 31), kind='employment')
    ContractClause.objects.create(
        contract=contract,
        name='fishers',
        kind='contract-clauses-parties-requirement-fishers',
        content={'vessel': vessel.app_ref},
    )
    return contract


class WorkerSyncDataTestCase(TestCase):
    def setUp(self):
        self.vessel = Vessel.objects.create(app_ref='vessel-1', name='Vessel One', reg_no='REG-1')
        self.contract = make_contract_with_vessel(self.vessel)
        self.worker = make_user('worker@example.com', group_name='worker')
        UserContractAccess.objects.create(user=self.worker, contract=self.contract)
        Wage.objects.create(
            vessel=self.vessel, user=self.worker,
            payment_date=date(2024, 1, 1), start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            usd_amount=100,
        )

        self.other_worker = make_user('other-worker@example.com', group_name='worker')
        other_vessel = Vessel.objects.create(app_ref='vessel-2', name='Vessel Two', reg_no='REG-2')
        other_contract = make_contract_with_vessel(other_vessel, name='other-contract')
        UserContractAccess.objects.create(user=self.other_worker, contract=other_contract)
        Wage.objects.create(
            vessel=other_vessel, user=self.other_worker,
            payment_date=date(2024, 1, 1), start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            usd_amount=200,
        )

    def test_worker_only_sees_own_contract_and_vessel(self):
        data = get_sync_data(self.worker)

        self.assertEqual(len(data['contracts']), 1)
        self.assertEqual(data['contracts'][0]['id'], self.contract.id)
        self.assertEqual([v['app_ref'] for v in data['vessels']], ['vessel-1'])

    def test_worker_only_sees_own_wages(self):
        data = get_sync_data(self.worker)

        self.assertEqual(len(data['wages']), 1)
        self.assertEqual(data['wages'][0]['user'], self.worker.id)


class VesselOwnerSyncDataTestCase(TestCase):
    def setUp(self):
        self.vessel_owner = make_user('vo@example.com', group_name='vessel_owner')
        self.other_vessel_owner = make_user('other-vo@example.com', group_name='vessel_owner')

        self.company = Company.objects.create(name='Acme', created_by=self.vessel_owner.id)
        Company.objects.create(name='Other Co', created_by=self.other_vessel_owner.id)

        self.vessel = Vessel.objects.create(
            app_ref='vo-vessel', name='VO Vessel', reg_no='REG-VO', created_by=self.vessel_owner.id)
        Vessel.objects.create(
            app_ref='other-vessel', name='Other Vessel', reg_no='REG-OTHER', created_by=self.other_vessel_owner.id)

        self.added_worker = make_user('added-worker@example.com', group_name='worker')
        self.added_worker.created_by = self.vessel_owner.id
        self.added_worker.save()
        Wage.objects.create(
            vessel=self.vessel, user=self.added_worker,
            payment_date=date(2024, 1, 1), start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            usd_amount=150,
        )

        self.unrelated_worker = make_user('unrelated-worker@example.com', group_name='worker')

        self.agent = make_user('agent@example.com', group_name='taiwanese_agent')
        AgentVesselOwnerRelationship.objects.create(
            agent=self.agent, vessel_owner=self.vessel_owner, status='active')

    def test_vessel_owner_only_sees_own_companies_and_vessels(self):
        data = get_sync_data(self.vessel_owner)

        self.assertEqual([c['name'] for c in data['companies']], ['Acme'])
        self.assertEqual([v['app_ref'] for v in data['vessels']], ['vo-vessel'])

    def test_vessel_owner_sees_added_worker_and_linked_agent_but_not_unrelated_users(self):
        data = get_sync_data(self.vessel_owner)

        user_ids = {u['id'] for u in data['users']}
        self.assertIn(self.vessel_owner.id, user_ids)
        self.assertIn(self.added_worker.id, user_ids)
        self.assertIn(self.agent.id, user_ids)
        self.assertNotIn(self.unrelated_worker.id, user_ids)

    def test_vessel_owner_only_sees_wages_of_added_users(self):
        data = get_sync_data(self.vessel_owner)

        self.assertEqual(len(data['wages']), 1)
        self.assertEqual(data['wages'][0]['user'], self.added_worker.id)


class AgentSyncDataTestCase(TestCase):
    def setUp(self):
        self.agent = make_user('agent2@example.com', group_name='indonesian_agent')
        self.recruited_worker = make_user(
            'recruited@example.com', group_name='worker', recruited_by=self.agent)
        self.unrecruited_worker = make_user('unrecruited@example.com', group_name='worker')

        self.vessel_owner = make_user('vo2@example.com', group_name='vessel_owner')
        AgentVesselOwnerRelationship.objects.create(
            agent=self.agent, vessel_owner=self.vessel_owner, status='active')

        vessel = Vessel.objects.create(app_ref='agent-vessel', name='Agent Vessel', reg_no='REG-AG')
        Wage.objects.create(
            vessel=vessel, user=self.recruited_worker,
            payment_date=date(2024, 1, 1), start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            usd_amount=120,
        )
        Wage.objects.create(
            vessel=vessel, user=self.unrecruited_worker,
            payment_date=date(2024, 1, 1), start_date=date(2024, 1, 1), end_date=date(2024, 1, 31),
            usd_amount=300,
        )

    def test_agent_sees_recruited_worker_and_linked_vessel_owner_but_not_others(self):
        data = get_sync_data(self.agent)

        user_ids = {u['id'] for u in data['users']}
        self.assertIn(self.agent.id, user_ids)
        self.assertIn(self.recruited_worker.id, user_ids)
        self.assertIn(self.vessel_owner.id, user_ids)
        self.assertNotIn(self.unrecruited_worker.id, user_ids)

    def test_agent_only_sees_wages_of_recruited_users(self):
        data = get_sync_data(self.agent)

        self.assertEqual(len(data['wages']), 1)
        self.assertEqual(data['wages'][0]['user'], self.recruited_worker.id)


class DefaultAndAdminSyncDataTestCase(TestCase):
    def setUp(self):
        self.public_user = make_user('public@example.com', group_name='public')
        self.other_user = make_user('other-public@example.com', group_name='public')
        self.superuser = User.objects.create_superuser(email='admin@example.com', password='password123')

        Company.objects.create(name='Some Co', created_by=self.other_user.id)
        Vessel.objects.create(app_ref='some-vessel', name='Some Vessel', reg_no='REG-SOME')

    def test_default_role_only_gets_own_data_no_workspace_wide_access(self):
        data = get_sync_data(self.public_user)

        self.assertNotIn('companies', data)
        self.assertNotIn('vessels', data)
        self.assertNotIn('users', data)
        self.assertEqual(data['contracts'], [])

    def test_superuser_gets_everything(self):
        data = get_sync_data(self.superuser)

        user_ids = {u['id'] for u in data['users']}
        self.assertIn(self.public_user.id, user_ids)
        self.assertIn(self.other_user.id, user_ids)
        self.assertEqual(len(data['companies']), 1)
        self.assertEqual(len(data['vessels']), 1)
