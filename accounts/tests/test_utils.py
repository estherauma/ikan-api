from datetime import date, timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from accounts.models import AgentVesselOwnerRelationship, User, UserBank, UserBeneficiaries
from accounts.sync_utils import get_sync_data, sync_push_data
from companies.models import Company
from contracts.models import Contract, ContractClause, UserContractAccess
from mydocuments.models import Document
from notifications.models import Notification
from survey.models import LearningHubProgress, Survey
from vessels.models import Vessel, VesselImage
from wages.models import Wage


def age_record(instance, when):
    """Backdate/forward-date a record's updated_at, bypassing auto_now (which .save() would overwrite)."""
    type(instance).objects.filter(pk=instance.pk).update(updated_at=when)


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

        self.company = Company.objects.create(name='Acme', created_by=self.vessel_owner)
        Company.objects.create(name='Other Co', created_by=self.other_vessel_owner)

        self.vessel = Vessel.objects.create(
            app_ref='vo-vessel', name='VO Vessel', reg_no='REG-VO', created_by=self.vessel_owner)
        Vessel.objects.create(
            app_ref='other-vessel', name='Other Vessel', reg_no='REG-OTHER', created_by=self.other_vessel_owner)

        self.added_worker = make_user('added-worker@example.com', group_name='worker')
        self.added_worker.created_by = self.vessel_owner
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

        Company.objects.create(name='Some Co', created_by=self.other_user)
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


class DeltaSyncTestCase(TestCase):
    """Covers the `last_synced_at` delta-sync filtering added to get_sync_data() and its helpers."""

    def setUp(self):
        self.vessel_owner = make_user('delta-vo@example.com', group_name='vessel_owner')
        self.cutoff = timezone.now()

    def test_no_cutoff_returns_everything(self):
        company = Company.objects.create(name='Full Co', created_by=self.vessel_owner)
        age_record(company, self.cutoff - timedelta(days=30))

        data = get_sync_data(self.vessel_owner)

        self.assertEqual([c['name'] for c in data['companies']], ['Full Co'])

    def test_unchanged_company_excluded_after_cutoff(self):
        company = Company.objects.create(name='Old Co', created_by=self.vessel_owner)
        age_record(company, self.cutoff - timedelta(days=1))

        data = get_sync_data(self.vessel_owner, self.cutoff)

        self.assertEqual(data['companies'], [])

    def test_changed_company_included_after_cutoff(self):
        company = Company.objects.create(name='New Co', created_by=self.vessel_owner)
        age_record(company, self.cutoff + timedelta(days=1))

        data = get_sync_data(self.vessel_owner, self.cutoff)

        self.assertEqual([c['name'] for c in data['companies']], ['New Co'])

    def test_vessel_included_when_only_its_image_changed(self):
        vessel = Vessel.objects.create(
            app_ref='delta-vessel', name='Delta Vessel', reg_no='REG-DELTA', created_by=self.vessel_owner)
        age_record(vessel, self.cutoff - timedelta(days=1))
        image = VesselImage.objects.create(app_ref='delta-image', vessel=vessel, image_url='vessels/delta.png')
        age_record(image, self.cutoff + timedelta(days=1))

        data = get_sync_data(self.vessel_owner, self.cutoff)

        self.assertEqual([v['app_ref'] for v in data['vessels']], ['delta-vessel'])

    def test_vessel_excluded_when_neither_it_nor_its_image_changed(self):
        vessel = Vessel.objects.create(
            app_ref='stale-vessel', name='Stale Vessel', reg_no='REG-STALE', created_by=self.vessel_owner)
        age_record(vessel, self.cutoff - timedelta(days=1))
        image = VesselImage.objects.create(app_ref='stale-image', vessel=vessel, image_url='vessels/stale.png')
        age_record(image, self.cutoff - timedelta(days=1))

        data = get_sync_data(self.vessel_owner, self.cutoff)

        self.assertEqual(data['vessels'], [])

    def test_contract_included_when_only_a_clause_changed(self):
        contract = Contract.objects.create(
            name='Delta Contract', app_ref='delta-contract', start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31), kind='employment', created_by=self.vessel_owner)
        age_record(contract, self.cutoff - timedelta(days=1))
        clause = ContractClause.objects.create(contract=contract, name='clause', kind='other', content='{}')
        age_record(clause, self.cutoff + timedelta(days=1))

        data = get_sync_data(self.vessel_owner, self.cutoff)

        self.assertEqual([c['app_ref'] for c in data['contracts']], ['delta-contract'])
        self.assertEqual(len(data['contract_clauses']), 1)

    def test_user_included_when_only_bank_account_changed(self):
        worker = make_user('delta-worker@example.com', group_name='worker')
        worker.created_by = self.vessel_owner
        worker.save()
        age_record(worker, self.cutoff - timedelta(days=1))
        bank = UserBank.objects.create(user=worker, account_name='x', account_number='1')
        age_record(bank, self.cutoff + timedelta(days=1))

        data = get_sync_data(self.vessel_owner, self.cutoff)

        self.assertIn(worker.id, {u['id'] for u in data['users']})

    def test_user_excluded_when_neither_profile_nor_bank_details_changed(self):
        worker = make_user('stale-worker@example.com', group_name='worker')
        worker.created_by = self.vessel_owner
        worker.save()
        age_record(worker, self.cutoff - timedelta(days=1))
        bank = UserBank.objects.create(user=worker, account_name='x', account_number='1')
        age_record(bank, self.cutoff - timedelta(days=1))

        data = get_sync_data(self.vessel_owner, self.cutoff)

        self.assertNotIn(worker.id, {u['id'] for u in data['users']})

    def test_own_data_filtered_by_cutoff(self):
        worker = make_user('delta-doc-worker@example.com', group_name='worker')
        old_doc = Document.objects.create(
            app_ref='old-doc', user=worker, file_name='old.pdf', file_url='docs/old.pdf', doc_type='id')
        age_record(old_doc, self.cutoff - timedelta(days=1))
        new_doc = Document.objects.create(
            app_ref='new-doc', user=worker, file_name='new.pdf', file_url='docs/new.pdf', doc_type='id')
        age_record(new_doc, self.cutoff + timedelta(days=1))

        data = get_sync_data(worker, self.cutoff)

        self.assertEqual([d['file_name'] for d in data['documents']], ['new.pdf'])


class SyncPushDataTestCase(TestCase):
    def setUp(self):
        self.worker = make_user('push-worker@example.com', group_name='worker')
        self.vessel_owner = make_user('push-vo@example.com', group_name='vessel_owner')
        self.added_worker = make_user('push-added-worker@example.com', group_name='worker')
        self.added_worker.created_by = self.vessel_owner
        self.added_worker.save()
        self.unmanaged_worker = make_user('push-unmanaged-worker@example.com', group_name='worker')
        self.vessel = Vessel.objects.create(app_ref='push-vessel', name='Push Vessel', reg_no='REG-PUSH')

    def test_worker_can_create_own_survey_response(self):
        result = sync_push_data(self.worker, {
            'survey_responses': [{
                'app_ref': 'survey-1',
                'survey_date': '2024-01-01',
                'question_key': 'q1',
                'question_text': 'How are you?',
                'question_response': 'good',
            }],
        })

        self.assertEqual(len(result['pushed_data']['survey_responses']), 1)
        self.assertTrue(result['survey_synced'])
        survey = Survey.objects.get(app_ref='survey-1')
        self.assertEqual(survey.user_id, self.worker.id)

    def test_worker_cannot_set_another_user_as_the_owner(self):
        sync_push_data(self.worker, {
            'survey_responses': [{
                'app_ref': 'survey-2',
                'user': self.unmanaged_worker.id,
                'survey_date': '2024-01-01',
                'question_key': 'q1',
                'question_text': 'How are you?',
                'question_response': 'good',
            }],
        })

        survey = Survey.objects.get(app_ref='survey-2')
        self.assertEqual(survey.user_id, self.worker.id)

    def test_stale_offline_update_is_ignored(self):
        sync_push_data(self.worker, {
            'survey_responses': [{
                'app_ref': 'survey-3',
                'survey_date': '2024-01-01',
                'question_key': 'q1',
                'question_text': 'How are you?',
                'question_response': 'good',
            }],
        })
        survey = Survey.objects.get(app_ref='survey-3')
        stale_updated_at = (survey.updated_at.replace(year=survey.updated_at.year - 1)).isoformat()

        sync_push_data(self.worker, {
            'survey_responses': [{
                'app_ref': 'survey-3',
                'updated_at': stale_updated_at,
                'question_response': 'stale-update',
            }],
        })

        survey.refresh_from_db()
        self.assertEqual(survey.question_response, 'good')

    def test_vessel_owner_can_push_wage_for_added_worker(self):
        result = sync_push_data(self.vessel_owner, {
            'wages': [{
                'vessel': self.vessel.id,
                'user': self.added_worker.id,
                'payment_date': '2024-01-01',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'usd_amount': '100.00',
            }],
        })

        self.assertEqual(len(result['pushed_data']['wages']), 1)
        self.assertEqual(Wage.objects.filter(user=self.added_worker).count(), 1)

    def test_vessel_owner_cannot_push_wage_for_unmanaged_worker(self):
        with self.assertRaises(PermissionDenied):
            sync_push_data(self.vessel_owner, {
                'wages': [{
                    'vessel': self.vessel.id,
                    'user': self.unmanaged_worker.id,
                    'payment_date': '2024-01-01',
                    'start_date': '2024-01-01',
                    'end_date': '2024-01-31',
                    'usd_amount': '100.00',
                }],
            })


class SyncPushDataExtendedTestCase(TestCase):
    def setUp(self):
        self.vessel_owner = make_user('ext-vo@example.com', group_name='vessel_owner')
        self.worker = make_user('ext-worker@example.com', group_name='worker')
        self.added_worker = make_user('ext-added-worker@example.com', group_name='worker')
        self.added_worker.created_by = self.vessel_owner
        self.added_worker.save()
        self.unmanaged_worker = make_user('ext-unmanaged-worker@example.com', group_name='worker')

    def test_worker_cannot_push_company_vessel_or_contract(self):
        for key, record in (
            ('companies', {'app_ref': 'c-1', 'name': 'Blocked Co'}),
            ('vessels', {'app_ref': 'v-1', 'name': 'Blocked Vessel', 'reg_no': 'REG-B'}),
            ('contracts', {
                'app_ref': 'k-1', 'name': 'Blocked Contract', 'kind': 'employment',
                'start_date': '2024-01-01', 'end_date': '2024-12-31',
            }),
        ):
            with self.assertRaises(PermissionDenied):
                sync_push_data(self.worker, {key: [record]})

    def test_vessel_owner_can_push_company_and_vessel(self):
        result = sync_push_data(self.vessel_owner, {
            'companies': [{
                'app_ref': 'company-1', 'name': 'Acme', 'email': 'acme@example.com',
                'telephone': '123', 'country': 'PH', 'address_line_1': 'Main St',
            }],
            'vessels': [{
                'app_ref': 'vessel-1', 'name': 'Sea Star', 'reg_no': 'REG-1',
                'vessel_type': 'fishing', 'status': 'active', 'commissioning_date': '2024-01-01',
            }],
        })

        self.assertEqual(len(result['pushed_data']['companies']), 1)
        self.assertEqual(len(result['pushed_data']['vessels']), 1)
        company = Company.objects.get(app_ref='company-1')
        vessel = Vessel.objects.get(app_ref='vessel-1')
        self.assertEqual(company.created_by, self.vessel_owner)
        self.assertEqual(vessel.created_by, self.vessel_owner)

        # Pushing again with online_ref should update the same row, not create a new one.
        result = sync_push_data(self.vessel_owner, {
            'companies': [{'online_ref': company.id, 'app_ref': 'company-1', 'name': 'Acme Renamed'}],
        })
        self.assertEqual(Company.objects.filter(app_ref='company-1').count(), 1)
        self.assertEqual(result['pushed_data']['companies'][0]['name'], 'Acme Renamed')

    def test_vessel_owner_can_push_contract_with_nested_clauses(self):
        result = sync_push_data(self.vessel_owner, {
            'contracts': [{
                'app_ref': 'contract-1', 'name': 'Fishing Contract', 'kind': 'employment',
                'start_date': '2024-01-01', 'end_date': '2024-12-31',
                'clauses': [{'app_ref': 'clause-1', 'name': 'Term', 'kind': 'general', 'content': {}}],
            }],
        })

        contract = Contract.objects.get(app_ref='contract-1')
        self.assertEqual(contract.created_by, self.vessel_owner)
        self.assertEqual(ContractClause.objects.filter(contract=contract).count(), 1)
        self.assertEqual(len(result['pushed_data']['contracts'][0]['clauses']), 1)

    def test_profile_push_updates_own_profile_and_bank_details(self):
        result = sync_push_data(self.worker, {
            'profiles': [{
                'online_ref': self.worker.id,
                'first_name': 'Updated',
                'bank_accounts': [{'app_ref': 'bank-1', 'account_name': 'Worker', 'account_number': '123'}],
                'beneficiaries': [{'app_ref': 'ben-1', 'account_name': 'Ben', 'account_number': '456'}],
            }],
        })

        self.worker.refresh_from_db()
        self.assertEqual(self.worker.first_name, 'Updated')
        self.assertEqual(UserBank.objects.filter(user=self.worker, app_ref='bank-1').count(), 1)
        self.assertEqual(UserBeneficiaries.objects.filter(user=self.worker, app_ref='ben-1').count(), 1)
        profile_data = result['pushed_data']['profiles'][0]
        self.assertEqual(len(profile_data['bank_accounts']), 1)
        self.assertEqual(len(profile_data['beneficiaries']), 1)

    def test_vessel_owner_can_push_profile_for_added_worker(self):
        sync_push_data(self.vessel_owner, {
            'profiles': [{'online_ref': self.added_worker.id, 'first_name': 'Managed'}],
        })

        self.added_worker.refresh_from_db()
        self.assertEqual(self.added_worker.first_name, 'Managed')

    def test_profile_push_for_unmanaged_user_currently_succeeds(self):
        """The managed-worker ownership check in _get_syncable_user is temporarily disabled."""
        result = sync_push_data(self.vessel_owner, {
            'profiles': [{'online_ref': self.unmanaged_worker.id, 'first_name': 'Nope'}],
        })

        self.assertIn('profiles', result['pushed_data'])
        self.unmanaged_worker.refresh_from_db()
        self.assertEqual(self.unmanaged_worker.first_name, 'Nope')

    def test_notification_push_can_update_another_users_notification(self):
        other_user_notification = Notification.objects.create(
            user=self.unmanaged_worker, title='Not yours', message='msg', status='unread')

        result = sync_push_data(self.worker, {
            'notifications': [
                {'app_ref': 'notif-1', 'title': 'Mine', 'message': 'msg', 'status': 'unread'},
                {'online_ref': other_user_notification.id, 'title': 'Hijacked', 'message': 'msg', 'status': 'read'},
            ],
        })

        self.assertEqual(len(result['pushed_data']['notifications']), 2)
        other_user_notification.refresh_from_db()
        self.assertEqual(other_user_notification.title, 'Hijacked')
        self.assertEqual(other_user_notification.user_id, self.unmanaged_worker.id)
        self.assertEqual(Notification.objects.get(app_ref='notif-1').user_id, self.worker.id)

    def test_learning_hub_progress_pushed_as_single_object(self):
        result = sync_push_data(self.worker, {
            'learning_hub_progress': {'progress_data': [{'chapter': 1, 'complete': True}]},
        })

        self.assertEqual(LearningHubProgress.objects.filter(user=self.worker).count(), 1)
        self.assertNotIsInstance(result['pushed_data']['learning_hub_progress'], list)

    def test_learning_hub_progress_updates_existing_record_and_uses_request_user(self):
        # Create initial record
        sync_push_data(self.worker, {
            'learning_hub_progress': {'progress_data': [{'chapter': 1, 'complete': True}]},
        })
        self.assertEqual(LearningHubProgress.objects.filter(user=self.worker).count(), 1)

        # Push update without online_ref/app_ref and with an attempt to set another user
        result = sync_push_data(self.worker, {
            'learning_hub_progress': {
                'user': self.unmanaged_worker.id,
                'progress_data': [{'chapter': 1, 'complete': True}, {'chapter': 2, 'complete': True}],
            },
        })

        self.assertEqual(LearningHubProgress.objects.filter(user=self.worker).count(), 1)
        self.assertEqual(LearningHubProgress.objects.filter(user=self.unmanaged_worker).count(), 0)

        progress = LearningHubProgress.objects.get(user=self.worker)
        self.assertEqual(len(progress.progress_data), 2)
        self.assertEqual(progress.progress_data[1]['chapter'], 2)
        self.assertEqual(result['pushed_data']['learning_hub_progress']['progress_data'], progress.progress_data)

    def test_one_bad_record_does_not_abort_the_rest_of_the_section_or_other_sections(self):
        result = sync_push_data(self.worker, {
            'survey_responses': [
                {
                    'app_ref': 'survey-good',
                    'survey_date': '2024-01-01',
                    'question_key': 'q1',
                    'question_text': 'How are you?',
                    'question_response': 'good',
                },
                {'app_ref': 'survey-bad'},  # missing required fields
            ],
            'notifications': [{'app_ref': 'notif-ok', 'title': 'Hi', 'message': 'msg', 'status': 'unread'}],
        })

        self.assertEqual(len(result['pushed_data']['survey_responses']), 1)
        self.assertEqual(len(result['errors']['survey_responses']), 1)
        self.assertEqual(len(result['pushed_data']['notifications']), 1)
        self.assertFalse(result['survey_synced'])
