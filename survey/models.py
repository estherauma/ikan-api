from django.db import models
from common.models import AuditableModel
import json
from accounts.models import User
from common.utils import generate_uuid


class Survey(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET(User.objects.get_default_user),
        related_name="surveys",
        null=True,
        blank=True,
    )
    survey_date = models.DateField(null=False, blank=False)
    question_key = models.CharField(max_length=255, null=False, blank=False)
    question_type = models.TextField(max_length=255, null=True, blank=False)
    question_text = models.TextField(max_length=255, null=False, blank=False)
    question_response = models.TextField(null=False, blank=False)
    other_input = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_key = models.CharField(max_length=255, null=True, blank=True)
    follow_up_question_type = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_text = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_response = models.TextField(null=True, blank=True)
    follow_up_question_other_input = models.TextField(max_length=255, null=True, blank=True)
    second_follow_up_question_key = models.CharField(max_length=255, null=True, blank=True)
    second_follow_up_question_type = models.TextField(max_length=255, null=True, blank=True)
    second_follow_up_question_text = models.TextField(max_length=255, null=True, blank=True)
    second_follow_up_question_response = models.TextField(null=True, blank=True)
    second_follow_up_question_other_input = models.TextField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.question_text

    def get_question_response(self):
        return json.loads(self.question_response)

    def set_question_response(self, value):
        self.question_response = json.dumps(value)


class InlineQuestion(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET(User.objects.get_default_user),
        related_name="inline_questions",
    )
    question_key = models.CharField(max_length=255, null=False, blank=False)
    question_type = models.TextField(max_length=255, null=False, blank=False)
    question_text = models.TextField(max_length=255, null=False, blank=False)
    question_response = models.TextField(null=False, blank=False)
    sub_chapter = models.CharField(max_length=255, null=False, blank=False)
    other_input = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_key = models.CharField(max_length=255, null=True, blank=True)
    follow_up_question_type = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_text = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_response = models.TextField(null=True, blank=True)
    follow_up_question_other_input = models.TextField(max_length=255, null=True, blank=True)
    second_follow_up_question_key = models.CharField(max_length=255, null=True, blank=True)
    second_follow_up_question_type = models.TextField(max_length=255, null=True, blank=True)
    second_follow_up_question_text = models.TextField(max_length=255, null=True, blank=True)
    second_follow_up_question_response = models.TextField(null=True, blank=True)
    second_follow_up_question_other_input = models.TextField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.question_text


class LearningHubProgress(AuditableModel):
    app_ref = models.CharField(max_length=40, default=generate_uuid, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    progress_data = models.JSONField(default=list)

    def __str__(self):
        if self.user.name_on_contract:
            return f'Learning hub progress data for {self.user.name_on_contract}.'
        return f'Learning hub progress data for {self.user.first_name} {self.user.last_name}.'
