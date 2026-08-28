from datetime import timedelta
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from content.models import AggregatedContent
from content.services.aggregators import aggregate_documents
from content.services.content_aggregation import ContentAggregationService
from content.views import AggregatedContentView, UpdatedContentView, compare_content, serialize_aggregated_content


class AggregatorsTests(TestCase):
    @patch("content.services.aggregators.config", return_value="https://cms.example.com")
    def test_aggregate_documents_groups_page_content_by_locale_and_uid(self, _config):
        aggregated_data, aggregated_count = aggregate_documents(
            [
                {
                    "id": 101,
                    "custom_type": "page",
                    "uid": "home",
                    "locale": "en-us",
                    "page_title": "Home",
                    "dynamic_zone": [],
                },
                {
                    "id": 102,
                    "custom_type": "page",
                    "uid": "home",
                    "locale": "id-id",
                    "page_title": "Beranda",
                    "dynamic_zone": [],
                },
            ]
        )

        self.assertEqual(aggregated_count, 2)
        self.assertEqual(aggregated_data["en-us"]["home"]["page_title"], "Home")
        self.assertEqual(aggregated_data["id-id"]["home"]["page_title"], "Beranda")

    @patch("content.services.aggregators.config", return_value="https://cms.example.com")
    def test_aggregate_documents_filters_by_custom_type(self, _config):
        aggregated_data, aggregated_count = aggregate_documents(
            [
                {
                    "id": 101,
                    "custom_type": "page",
                    "uid": "home",
                    "locale": "en-us",
                    "page_title": "Home",
                    "dynamic_zone": [],
                },
                {
                    "id": 201,
                    "custom_type": "menu_content",
                    "uid": "sidemenu",
                    "locale": "en-us",
                    "page_title": "Side menu",
                    "dynamic_zone": [],
                },
            ],
            custom_type="menu_content",
        )

        self.assertEqual(aggregated_count, 1)
        self.assertNotIn("home", aggregated_data.get("en-us", {}))
        self.assertIn("sidemenu", aggregated_data["en-us"])

    @patch("content.services.aggregators.config", return_value="https://cms.example.com")
    def test_aggregate_documents_includes_video_area_components_from_strapi(self, _config):
        aggregated_data, aggregated_count = aggregate_documents(
            [
                {
                    "id": 240,
                    "custom_type": "create_content_area",
                    "uid": "tfa-training-video",
                    "locale": "en-us",
                    "page_title": "Know Your Rights Video & Quiz",
                    "dynamic_zone": [
                        {
                            "id": 4,
                            "thumbnail": None,
                            "video_link": "https://www.youtube.com/watch?v=lJJe1QS2wIE",
                            "__component": "ikan.video-area",
                        }
                    ],
                },
            ]
        )

        self.assertEqual(aggregated_count, 1)
        video_area = aggregated_data["en-us"]["tfa-training-video"]["pageContent"][0]
        self.assertEqual(video_area["type"], "video")
        self.assertEqual(
            video_area["mediaData"],
            {
                "url": "https://www.youtube.com/watch?v=lJJe1QS2wIE",
                "kind": "web",
            },
        )
        self.assertIsNone(video_area["thumbnail"])

    @patch("content.services.aggregators.config", return_value="https://cms.example.com")
    def test_aggregate_learning_hub_subchapter_attaches_second_follow_up_question(self, _config):
        aggregated_data, aggregated_count = aggregate_documents(
            [
                {
                    "id": 279,
                    "custom_type": "learning_hub_subchapter",
                    "uid": "subchapter-4.1",
                    "locale": "en-us",
                    "page_title": "Subchapter 4.1",
                    "dynamic_zone": [
                        {
                            "id": 1,
                            "__component": "ikan.question",
                            "question_key": "work_past_end_Date",
                            "question": [
                                {
                                    "type": "paragraph",
                                    "children": [
                                        {
                                            "type": "text",
                                            "text": "Did you continue to work past the end date described in the contract?",
                                        }
                                    ],
                                }
                            ],
                            "is_required": True,
                            "question_type": "radio",
                            "question_audio": None,
                            "roles": None,
                            "display_question": True,
                            "repeatable_zone": [
                                {
                                    "options": "Yes",
                                    "option_description": None,
                                    "roles": None,
                                    "follow_up_question": "Did you agree to this extended work period?",
                                    "follow_up_question_key": "agree_extend_work",
                                    "follow_up_question_link": "",
                                    "follow_up_question_type": "radio",
                                    "display_followup_question": True,
                                    "follow_up_question_options": "Yes\nNo",
                                    "is_required": True,
                                },
                                {
                                    "options": "No",
                                    "option_description": None,
                                    "roles": None,
                                    "follow_up_question": None,
                                    "follow_up_question_key": "no_extend",
                                    "follow_up_question_link": "",
                                    "follow_up_question_type": "text",
                                    "display_followup_question": True,
                                    "follow_up_question_options": None,
                                    "is_required": True,
                                },
                            ],
                        },
                        {
                            "id": 2,
                            "__component": "ikan.second-follow-up-question",
                            "roles": None,
                            "is_required": False,
                            "question_key": "work_past_end_Date",
                            "follow_up_question_key": "agree_extend_work",
                            "follow_up_question_option": "No",
                            "second_follow_up_question": "Get help here",
                            "second_follow_up_question_key": "get_help_no_agree_extend",
                            "second_follow_up_question_link": "/help",
                            "second_follow_up_question_type": "link",
                            "display_second_followup_question": True,
                            "second_follow_up_question_options": None,
                        },
                    ],
                },
            ]
        )

        self.assertEqual(aggregated_count, 1)
        question = aggregated_data["en-us"]["subchapter-4.1"]["pageContent"][0]
        second_follow_up = question["options"][0]["followUpQuestion"]["options"][1]["secondFollowUpQuestion"]

        self.assertEqual(second_follow_up["key"], "get_help_no_agree_extend")
        self.assertEqual(second_follow_up["question"], "Get help here")
        self.assertEqual(second_follow_up["questionLink"], "/help")
        self.assertEqual(second_follow_up["questionType"], "link")

    @patch("content.services.aggregators.config", return_value="https://cms.example.com")
    def test_aggregate_learning_hub_subchapter_leaves_unmatched_second_follow_up_question_unattached(
        self,
        _config,
    ):
        aggregated_data, aggregated_count = aggregate_documents(
            [
                {
                    "id": 279,
                    "custom_type": "learning_hub_subchapter",
                    "uid": "subchapter-4.1",
                    "locale": "en-us",
                    "page_title": "Subchapter 4.1",
                    "dynamic_zone": [
                        {
                            "id": 1,
                            "__component": "ikan.question",
                            "question_key": "work_past_end_Date",
                            "question": [
                                {
                                    "type": "paragraph",
                                    "children": [
                                        {
                                            "type": "text",
                                            "text": "Did you continue to work past the end date described in the contract?",
                                        }
                                    ],
                                }
                            ],
                            "is_required": True,
                            "question_type": "radio",
                            "question_audio": None,
                            "roles": None,
                            "display_question": True,
                            "repeatable_zone": [
                                {
                                    "options": "Yes",
                                    "option_description": None,
                                    "roles": None,
                                    "follow_up_question": "Did you agree to this extended work period?",
                                    "follow_up_question_key": "agree_extend_work",
                                    "follow_up_question_link": "",
                                    "follow_up_question_type": "radio",
                                    "display_followup_question": True,
                                    "follow_up_question_options": "Yes\nNo",
                                    "is_required": True,
                                }
                            ],
                        },
                        {
                            "id": 2,
                            "__component": "ikan.second-follow-up-question",
                            "roles": None,
                            "is_required": False,
                            "question_key": "different_question_key",
                            "follow_up_question_key": "agree_extend_work",
                            "follow_up_question_option": "No",
                            "second_follow_up_question": "Get help here",
                            "second_follow_up_question_key": "get_help_no_agree_extend",
                            "second_follow_up_question_link": "/help",
                            "second_follow_up_question_type": "link",
                            "display_second_followup_question": True,
                            "second_follow_up_question_options": None,
                        },
                    ],
                },
            ]
        )

        self.assertEqual(aggregated_count, 1)
        question = aggregated_data["en-us"]["subchapter-4.1"]["pageContent"][0]
        self.assertIsNone(question["options"][0]["followUpQuestion"]["options"][1]["secondFollowUpQuestion"])


class ContentAggregationServiceTests(TestCase):
    def setUp(self):
        self.content_service = Mock()
        self.service = ContentAggregationService(content_service=self.content_service)
        self.service._delete_older_agg_content = Mock()

    def create_record(self, content, created_at=None, updated_at=None):
        record = AggregatedContent.objects.create(content=content)
        updates = {}
        if created_at is not None:
            updates["created_at"] = created_at
        if updated_at is not None:
            updates["updated_at"] = updated_at
        if updates:
            AggregatedContent.objects.filter(pk=record.pk).update(**updates)
            record.refresh_from_db()
        return record

    @patch("content.services.content_aggregation.aggregate_documents")
    def test_aggregate_content_saves_aggregated_documents(self, aggregate_documents_mock):
        self.content_service.get_all_documents.return_value = {"data": [{"id": 1}]}
        aggregate_documents_mock.return_value = (
            {"en-us": {"home": {"page_title": "Home"}}},
            1,
        )

        record, aggregated_count = self.service.aggregate_content(collection_name="ikans")

        self.assertEqual(aggregated_count, 1)
        self.assertEqual(record.content["en-us"]["home"]["page_title"], "Home")
        self.content_service.get_all_documents.assert_called_once_with(
            collection_name="ikans",
            params={},
        )

    @patch("content.services.content_aggregation.aggregate_documents")
    def test_handle_publish_event_requires_entry_id(self, aggregate_documents_mock):
        result = self.service.handle_publish_event(collection_name="ikans", payload={"entry": {}})

        self.assertIsNone(result)
        aggregate_documents_mock.assert_not_called()
        self.content_service.get_document.assert_not_called()

    @patch("content.services.content_aggregation.aggregate_documents")
    def test_handle_publish_event_merges_single_document_into_latest_content(self, aggregate_documents_mock):
        existing_content = {
            "en-us": {
                "existing-page": {"page_title": "Existing"},
                "home": {"page_title": "Old home"},
            }
        }
        existing_record = self.create_record(existing_content)
        self.content_service.get_document.return_value = {"data": {"id": 681}}
        aggregate_documents_mock.return_value = (
            {"en-us": {"home": {"page_title": "New home"}}},
            1,
        )

        record, aggregated_count = self.service.handle_publish_event(
            collection_name="ikans",
            payload={"entry": {"id": 681}},
        )

        self.assertEqual(record.pk, existing_record.pk)
        self.assertEqual(aggregated_count, 1)
        self.assertEqual(record.content["en-us"]["home"]["page_title"], "New home")
        self.assertEqual(record.content["en-us"]["existing-page"]["page_title"], "Existing")
        self.content_service.get_document.assert_called_once_with(
            {
                "collection_name": "ikans",
                "document_id": 681,
            }
        )

    @patch("content.services.content_aggregation.aggregate_documents")
    def test_handle_publish_event_returns_none_when_aggregation_is_empty(self, aggregate_documents_mock):
        self.content_service.get_document.return_value = {"data": {"id": 681}}
        aggregate_documents_mock.return_value = ({}, 0)

        result = self.service.handle_publish_event(
            collection_name="ikans",
            payload={"entry": {"id": 681}},
        )

        self.assertIsNone(result)

    def test_handle_remove_event_requires_uid_and_locale(self):
        result = self.service.handle_remove_event(
            collection_name="ikans",
            payload={"entry": {"uid": "home"}},
        )

        self.assertIsNone(result)

    def test_handle_remove_event_updates_latest_record_when_page_exists(self):
        existing_content = {
            "en-us": {
                "home": {"page_title": "Home"},
                "existing-page": {"page_title": "Existing"},
            }
        }
        existing_record = self.create_record(existing_content)

        record, removed_count = self.service.handle_remove_event(
            collection_name="ikans",
            payload={"entry": {"uid": "home", "locale": "en-us"}},
        )

        self.assertEqual(record.pk, existing_record.pk)
        self.assertEqual(removed_count, 1)
        self.assertNotIn("home", record.content["en-us"])
        self.assertIn("existing-page", record.content["en-us"])

    def test_handle_remove_event_removes_locale_when_last_page_deleted(self):
        self.create_record({"en-us": {"home": {"page_title": "Home"}}})

        record, removed_count = self.service.handle_remove_event(
            collection_name="ikans",
            payload={"entry": {"uid": "home", "locale": "en-us"}},
        )

        self.assertEqual(removed_count, 1)
        self.assertNotIn("en-us", record.content)

    def test_handle_remove_event_returns_zero_when_page_does_not_exist(self):
        self.create_record({"en-us": {"existing-page": {"page_title": "Existing"}}})

        result = self.service.handle_remove_event(
            collection_name="ikans",
            payload={"entry": {"uid": "home", "locale": "en-us"}},
        )

        self.assertEqual(result, (0, 0))

    def test_save_aggregated_content_updates_latest_record_within_retention_window(self):
        existing_record = self.create_record({"en-us": {"home": {"page_title": "Old"}}})

        record = self.service._save_aggregated_content(
            {"en-us": {"home": {"page_title": "Updated"}}}
        )

        self.assertEqual(record.pk, existing_record.pk)
        self.assertEqual(AggregatedContent.objects.count(), 1)
        self.assertEqual(record.content["en-us"]["home"]["page_title"], "Updated")

    def test_save_aggregated_content_creates_new_record_when_latest_is_older_than_retention(self):
        old_record = self.create_record(
            {"en-us": {"home": {"page_title": "Old"}}},
            created_at=timezone.now() - timedelta(days=2),
            updated_at=timezone.now() - timedelta(days=2),
        )

        record = self.service._save_aggregated_content(
            {"en-us": {"home": {"page_title": "New"}}}
        )

        self.assertNotEqual(record.pk, old_record.pk)
        self.assertTrue(AggregatedContent.objects.filter(pk=record.pk).exists())

    def test_delete_older_agg_content_removes_records_older_than_retention_window(self):
        old_record = self.create_record(
            {"en-us": {"old": {"page_title": "Old"}}},
            created_at=timezone.now() - timedelta(days=2),
            updated_at=timezone.now() - timedelta(days=2),
        )
        recent_record = self.create_record({"en-us": {"new": {"page_title": "New"}}})

        ContentAggregationService(content_service=self.content_service)._delete_older_agg_content()

        self.assertFalse(AggregatedContent.objects.filter(pk=old_record.pk).exists())
        self.assertTrue(AggregatedContent.objects.filter(pk=recent_record.pk).exists())


class ContentViewsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def create_record(self, content, created_at=None, updated_at=None):
        record = AggregatedContent.objects.create(content=content)
        updates = {}
        if created_at is not None:
            updates["created_at"] = created_at
        if updated_at is not None:
            updates["updated_at"] = updated_at
        if updates:
            AggregatedContent.objects.filter(pk=record.pk).update(**updates)
            record.refresh_from_db()
        return record

    def test_aggregated_content_view_returns_empty_list_when_no_content_exists(self):
        request = self.factory.get("/api/v1/content/aggregated/")
        response = AggregatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    def test_aggregated_content_view_returns_created_at_from_updated_at(self):
        record = self.create_record({"en-us": {"home": {"page_title": "Home"}}})
        serialized = serialize_aggregated_content(record)

        request = self.factory.get("/api/v1/content/aggregated/")
        response = AggregatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"][0]["created_at"], serialized["updated_at"])

    def test_compare_content_returns_400_when_timestamp_is_missing(self):
        request = self.factory.get("/api/v1/content/compare/")

        response = compare_content(request)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["new"])

    def test_compare_content_accepts_updated_at_query_param(self):
        record = self.create_record({"en-us": {"home": {"page_title": "Home"}}})
        serialized = serialize_aggregated_content(record)
        request = self.factory.get(
            "/api/v1/content/compare/",
            {"app_content_updated_at": serialized["updated_at"]},
        )

        response = compare_content(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["new"])

    def test_compare_content_accepts_legacy_created_at_query_param(self):
        record = self.create_record({"en-us": {"home": {"page_title": "Home"}}})
        serialized = serialize_aggregated_content(record)
        request = self.factory.get(
            "/api/v1/content/compare/",
            {"app_content_created_at": serialized["created_at"]},
        )

        response = compare_content(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["new"])

    def test_compare_content_accepts_query_param_when_timezone_plus_becomes_space(self):
        record = self.create_record({"en-us": {"home": {"page_title": "Home"}}})
        serialized = serialize_aggregated_content(record)
        broken_timestamp = serialized["updated_at"].replace("+", " ")
        request = self.factory.get(
            "/api/v1/content/compare/",
            {"app_content_updated_at": broken_timestamp},
        )

        response = compare_content(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["new"])

    def test_compare_content_returns_new_content_with_legacy_created_at_field(self):
        self.create_record({"en-us": {"home": {"page_title": "Home"}}})
        request = self.factory.get(
            "/api/v1/content/compare/",
            {"app_content_updated_at": "2020-01-01T00:00:00Z"},
        )

        response = compare_content(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["new"])
        self.assertEqual(
            response.data["data"][0]["created_at"],
            response.data["data"][0]["updated_at"],
        )

    @patch.object(UpdatedContentView, "STRAPI_WEBHOOK_API_KEY", None)
    def test_updated_content_view_requires_api_key_configuration(self):
        request = self.factory.post(
            "/api/v1/content/updated",
            {"model": "ikan", "event": "entry.publish", "entry": {"id": 1}},
            format="json",
        )

        response = UpdatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 500)

    @patch.object(UpdatedContentView, "STRAPI_WEBHOOK_API_KEY", "secret")
    def test_updated_content_view_rejects_invalid_api_key_header(self):
        request = self.factory.post(
            "/api/v1/content/updated",
            {"model": "ikan", "event": "entry.publish", "entry": {"id": 1}},
            format="json",
            HTTP_X_API_KEY="wrong",
        )

        response = UpdatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 403)

    @patch.object(UpdatedContentView, "STRAPI_WEBHOOK_API_KEY", "secret")
    @patch("content.views.ContentAggregationService")
    def test_updated_content_view_ignores_unsupported_model(self, service_cls):
        request = self.factory.post(
            "/api/v1/content/updated",
            {"model": "other", "event": "entry.publish", "entry": {"id": 1}},
            format="json",
            HTTP_X_API_KEY="secret",
        )

        response = UpdatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        service_cls.assert_not_called()

    @patch.object(UpdatedContentView, "STRAPI_WEBHOOK_API_KEY", "secret")
    @patch("content.views.ContentAggregationService")
    def test_updated_content_view_ignores_unsupported_event(self, service_cls):
        request = self.factory.post(
            "/api/v1/content/updated",
            {"model": "ikan", "event": "entry.unknown", "entry": {"id": 1}},
            format="json",
            HTTP_X_API_KEY="secret",
        )

        response = UpdatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        service_instance = service_cls.return_value
        service_instance.handle_publish_event.assert_not_called()
        service_instance.handle_remove_event.assert_not_called()

    @patch.object(UpdatedContentView, "STRAPI_WEBHOOK_API_KEY", "secret")
    @patch("content.views.ContentAggregationService")
    def test_updated_content_view_dispatches_publish_event(self, service_cls):
        service_instance = service_cls.return_value
        service_instance.handle_publish_event.return_value = (Mock(), 1)
        payload = {"model": "ikan", "event": "entry.publish", "entry": {"id": 681}}
        request = self.factory.post(
            "/api/v1/content/updated",
            payload,
            format="json",
            HTTP_X_API_KEY="secret",
        )

        response = UpdatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        service_instance.handle_publish_event.assert_called_once_with(
            collection_name="ikans",
            payload=payload,
        )

    @patch.object(UpdatedContentView, "STRAPI_WEBHOOK_API_KEY", "secret")
    @patch("content.views.ContentAggregationService")
    def test_updated_content_view_dispatches_remove_event(self, service_cls):
        service_instance = service_cls.return_value
        service_instance.handle_remove_event.return_value = (Mock(), 1)
        payload = {"model": "ikan", "event": "entry.unpublish", "entry": {"uid": "home", "locale": "en-us"}}
        request = self.factory.post(
            "/api/v1/content/updated",
            payload,
            format="json",
            HTTP_X_API_KEY="secret",
        )

        response = UpdatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        service_instance.handle_remove_event.assert_called_once_with(
            collection_name="ikans",
            payload=payload,
        )

    @patch.object(UpdatedContentView, "STRAPI_WEBHOOK_API_KEY", "secret")
    @patch("content.views.ContentAggregationService")
    def test_updated_content_view_returns_500_when_handler_fails(self, service_cls):
        service_instance = service_cls.return_value
        service_instance.handle_publish_event.return_value = None
        request = self.factory.post(
            "/api/v1/content/updated",
            {"model": "ikan", "event": "entry.publish", "entry": {"id": 681}},
            format="json",
            HTTP_X_API_KEY="secret",
        )

        response = UpdatedContentView.as_view()(request)

        self.assertEqual(response.status_code, 500)
