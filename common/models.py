from common.push_id import push_id
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    '''Base model'''
    id = models.CharField(max_length=20, primary_key=True,
                          default=push_id)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


def get_sentinel_user():
    """Lazily evaluates at deletion time to avoid circular imports."""
    User = get_user_model()
    return User.objects.get_default_user()


class AuditableModel(BaseModel):
    ''' Auditable base model '''
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        null=True,
        blank=True,
        # related_name="%(app_label)s_%(class)s_created",  # eg wages_wage_created for the Wage model in the wages app
        related_name="+"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        null=True,
        blank=True,
        # related_name="%(app_label)s_%(class)s_updated", # eg survey_inlinequestion_updated for the InlineQuestion \
        # model in the survey app
        related_name="+"
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        null=True,
        blank=True,
        # related_name="%(app_label)s_%(class)s_deleted",
        related_name="+"
    )

    class Meta:
        abstract = True
        # speeds up the mobile app's delta sync queries (filtering by updated_at since the last sync)
        indexes = [models.Index(fields=['updated_at'])]

    def soft_delete(self, user=None):
        """Marks a record deleted instead of removing the row, so delta syncs can see it as a tombstone."""
        self.deleted = True
        self.deleted_at = timezone.now()
        if user is not None and getattr(user, 'is_authenticated', False):
            self.deleted_by = user
        self.save()


auditable_fields = [
    'created_at',
    'updated_at',
    'deleted_at',
    'created_by',
    'updated_by',
    'deleted_by',
    'deleted',
]
