from django.db import models
from common.models import BaseModel

class ContractClauseType(BaseModel):
    name = models.CharField(max_length=100, null=False, blank=False)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
