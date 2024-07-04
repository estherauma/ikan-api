from django.db import models
from common.models import AuditableModel
from accounts.models import User


class Company(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=False)
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.CharField(max_length=255, null=False, blank=False)
    logo_url = models.CharField(max_length=255)
    status = models.CharField(max_length=255, null=True, blank=False)
    country = models.CharField(max_length=255)
    city = models.CharField(max_length=255, null=True, blank=False)
    telephone = models.CharField(max_length=255)
    email = models.EmailField(unique=False)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255)
    address_line_3 = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class UserCompany(AuditableModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.user.email} {self.company.name}'
