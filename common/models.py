from common.push_id import push_id
from django.db import models


class BaseModel(models.Model):
    '''Base model'''
    id = models.CharField(max_length=20, primary_key=True,
                          default=push_id)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

class AuditableModel(BaseModel):
    ''' Auditable base model '''
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=256, null=True, blank=True)
    updated_by = models.CharField(max_length=256, null=True, blank=True)
    deleted_by = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        abstract = True


auditable_fields = [
    'created_at',
    'updated_at',
    'deleted_at',
    'created_by',
    'updated_by',
    'deleted_by',
    'deleted',
]
