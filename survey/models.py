from django.db import models
from common.models import AuditableModel
import json

class Survey(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=False)
    survey_date = models.DateField(null=False, blank=False)
    question_key = models.CharField(max_length=255, null=False, blank=False)
    question_text = models.TextField(max_length=255, null=False, blank=False)
    question_response = models.TextField(null=False, blank=False)
    
    def __str__(self):
        return self.question_text

    def get_question_response(self):
        return json.loads(self.question_response)
    
    def set_question_response(self, value):
        self.question_response = json.dumps(value)