from django.db import models
from common.models import AuditableModel
import json
from accounts.models import User


class Survey(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='surveys', null=True, blank=True)
    survey_date = models.DateField(null=False, blank=False)
    question_key = models.CharField(max_length=255, null=False, blank=False)
    question_type = models.TextField(max_length=255, null=True, blank=False)
    question_text = models.TextField(max_length=255, null=False, blank=False)
    question_response = models.TextField(null=False, blank=False)
    follow_up_question_key = models.CharField(max_length=255, null=True, blank=True)
    follow_up_question_type = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_text = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_response = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.question_text

    def get_question_response(self):
        return json.loads(self.question_response)

    def set_question_response(self, value):
        self.question_response = json.dumps(value)


class InlineQuestion(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inline_questions')
    question_key = models.CharField(max_length=255, null=False, blank=False)
    question_type = models.TextField(max_length=255, null=False, blank=False)
    question_text = models.TextField(max_length=255, null=False, blank=False)
    question_response = models.TextField(null=False, blank=False)
    sub_chapter = models.CharField(max_length=255, null=False, blank=False)
    follow_up_question_key = models.CharField(max_length=255, null=True, blank=True)
    follow_up_question_type = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_text = models.TextField(max_length=255, null=True, blank=True)
    follow_up_question_response = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.question_text
