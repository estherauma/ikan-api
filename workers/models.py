from django.db import models
from common.models import AuditableModel
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from contracts.models import Contract
from vessels.models import Vessel
from agents.models import Agent


class Worker(AuditableModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worker')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='worker', null=True, blank=True)
    vessel = models.ForeignKey(Vessel, on_delete=models.CASCADE, related_name='worker', null=True, blank=True)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='agent', null=True, blank=True)
    app_ref = models.CharField(max_length=255, null=True, blank=False)
    f_name = models.CharField(_('First Name'), max_length=30)
    l_name = models.CharField(_('Last Name'), max_length=30)
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('Phone Number'), max_length=255)
    address_line_1 = models.CharField(_('Address Line 1'), max_length=255)
    address_line_2 = models.CharField(_('Address Line 2'), max_length=255, null=True, blank=True)
    address_line_3 = models.CharField(_('Address Line 3'), max_length=255, null=True, blank=True)
    city = models.CharField(_('City'), max_length=255)
    country = models.CharField(_('Country'), max_length=50)
    zip_code = models.CharField(_('Zip Code'), max_length=50)
    status = models.CharField(_('Status'), max_length=50)
    invite_sent = models.BooleanField(_('Invite Sent'), default=False)
    invite_accepted = models.BooleanField(_('Invite Accepted'), default=False)
    profile_img_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f'{self.f_name} {self.l_name}, {self.email}'
