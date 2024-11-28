from django.contrib import admin
from survey.models import Survey, InlineQuestion


class SurveyAdmin(admin.ModelAdmin):
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "app_ref",
    ]
    list_display_links = [
        "id",
        "user",
    ]
    list_display = [
        "id",
        "user",
        "survey_date",
        "question_text",
        "question_response",
        "question_key",
        "question_type",
        "follow_up_question_text",
        "follow_up_question_response",
        "follow_up_question_key",
        "follow_up_question_type",
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by",
        "updated_by",
        "deleted_by",
        "deleted",
        "app_ref",
    ]


class InlineQuestionAdmin(admin.ModelAdmin):
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "app_ref",
    ]
    list_display_links = [
        "id",
        "user",
    ]
    list_display = [
        "id",
        "user",
        "created_at",
        "question_text",
        "question_response",
        "question_key",
        "question_type",
        "follow_up_question_text",
        "follow_up_question_response",
        "follow_up_question_key",
        "follow_up_question_type",
        "sub_chapter",
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by",
        "updated_by",
        "deleted_by",
        "deleted",
        "app_ref",
    ]


admin.site.register(Survey, SurveyAdmin)
admin.site.register(InlineQuestion, InlineQuestionAdmin)
