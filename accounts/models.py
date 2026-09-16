from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from common.models import AuditableModel
from django.utils.translation import gettext_lazy as _
from common.models import BaseModel
from django.core.exceptions import ValidationError
from django.db.models import F, Q
import secrets
from django.contrib.auth import get_user_model
from accounts.utils import get_user_queryset


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        mobile = extra_fields.get('mobile')
        if not email and not mobile:
            raise ValueError('Email or phone number is required.')

        if email:
            extra_fields['email'] = self.normalize_email(email)
        else:
            # Ensures email isn't passed as an empty string since the model expects None
            extra_fields['email'] = None

        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    @classmethod
    def get_default_user(cls, *args, **kwargs):
        User = get_user_model()
        default_email = 'default_ikan_user@fiftyeight.io'

        user, created = User.objects.get_or_create(
            email=default_email,
            defaults={
                'is_active': False,
                'password': secrets.token_urlsafe(16),
            }
        )
        return user


class User(AbstractBaseUser, AuditableModel, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_verified = models.BooleanField(_('verified'), default=False)
    is_staff = models.BooleanField(default=False)
    reset_password_token = models.CharField(null=True, blank=True, max_length=125)
    reset_password_token_created_at = models.DateTimeField(null=True, blank=True)
    profile_image = models.ImageField(null=True, blank=True)
    access_code = models.CharField(_('access code'), null=True, blank=True, max_length=30)
    position = models.CharField(_('position'), null=True, blank=True, max_length=30)
    telephone = models.CharField(_('telephone'), unique=True, null=True, blank=True, max_length=30)
    is_telephone_verified = models.BooleanField(_('is telephone verified?'), default=False)
    mobile = models.CharField(_('mobile'), unique=True, null=True, blank=True, max_length=30)
    is_mobile_verified = models.BooleanField(_('Is mobile verified?'), default=False)
    address_line_1 = models.CharField(_('address line 1'), null=True, blank=True, max_length=30)
    address_line_2 = models.CharField(_('address line 2'), null=True, blank=True, max_length=30)
    address_line_3 = models.CharField(_('address line 3'), null=True, blank=True, max_length=30)
    city = models.CharField(_('city'), null=True, blank=True, max_length=30)
    country = models.CharField(_('country'), null=True, blank=True, max_length=30)
    postal_code = models.CharField(_('postal code'), null=True, blank=True, max_length=30)
    registration_number = models.CharField(_('registration number'), null=True, blank=True, max_length=30)
    passport_number = models.CharField(_('passport number'), null=True, blank=True, max_length=30)
    recruited_by = models.ForeignKey('self', on_delete=models.SET(UserManager.get_default_user), null=True, blank=True)

    USERNAME_FIELD = 'email'

    objects = UserManager()

    @property
    def is_admin(self):
        return self.is_superuser or self.groups.filter(name='admin').exists()

    @property
    def name_on_contract(self):
        name_on_contract = None
        if self.groups.filter(name='worker').exists():
            name_on_contract = self.user_contract_access.select_related('contract') \
                .values_list('contract__name', flat=True).first()
        return name_on_contract

    # This property is used to get the vessel owners associated with an agent.
    # It checks if the current user is an 'agent (taiwanese_agent or indonesian_agent)' and then
    # retrieves the vessel owners linked to that agent through the AgentVesselOwnerRelationship model.
    @property
    def vessel_owners(self):
        role_queryset = self.groups.filter(Q(name='taiwanese_agent') | Q(name='indonesian_agent'))
        if role_queryset.exists():
            vo_queryset = get_user_queryset().filter(agent_relationships__agent=self,
                                                     agent_relationships__status='active')
            return vo_queryset if vo_queryset.exists() else None
        return None

    # This property is used to get the agents associated with a vessel owner.
    # It checks if the current user is a 'vessel_owner' and then retrieves the agents
    # linked to that vessel owner through the AgentVesselOwnerRelationship model.
    @property
    def agents(self):
        if self.groups.filter(name='vessel_owner').exists():
            agent_queryset = get_user_queryset().filter(vessel_owner_relationships__vessel_owner=self,
                                                        vessel_owner_relationships__status='active')
            return agent_queryset if agent_queryset.exists() else None
        return None

    def __str__(self):
        if self.name_on_contract:
            return f'{self.name_on_contract} ({self.email or self.mobile or self.telephone})'

        return f'{self.first_name} {self.last_name} ({self.email or self.mobile or self.telephone})'

    def clean(self):
        super().clean()

        numbers = {}
        if self.mobile:
            mobile_clean = self.mobile.strip()
            if mobile_clean:
                numbers['mobile'] = mobile_clean
        if self.telephone:
            telephone_clean = self.telephone.strip()
            if telephone_clean:
                numbers['telephone'] = telephone_clean
        if not numbers:
            return

        # check for phone number uniqueness across all users
        existing_users = User.objects.filter(
            Q(mobile__in=numbers.values()) | Q(telephone__in=numbers.values())
        ).exclude(pk=self.pk)

        if existing_users.exists():
            errors = {}
            # Add all mobile & telephone numbers to a set to avoid duplicate queries to the db when iterating numbers
            conflicting_numbers = set()
            for user in existing_users:
                if user.mobile:
                    conflicting_numbers.add(user.mobile.strip())
                if user.telephone:
                    conflicting_numbers.add(user.telephone.strip())
            for field, value in numbers.items():
                if value in conflicting_numbers:
                    errors[field] = f"{value} is already registered to another user."
            if errors:
                raise ValidationError(errors)


class LoginEvent(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.SET(UserManager.get_default_user), related_name='login_events')
    ip_address = models.GenericIPAddressField()
    date_logged_in = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'login_events'

    def __str__(self) -> str:
        return f'{self.user.email or self.user.mobile or self.user.telephone}@{self.ip_address} \
            logged in at {self.date_logged_in}'


class UserBank(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=False)
    account_name = models.CharField(max_length=255, null=False, blank=False)
    account_number = models.CharField(max_length=255, null=False, blank=False)
    routing_number = models.CharField(max_length=255, null=True, blank=True)
    swift_code = models.CharField(max_length=255, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_branch = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user} - {self.account_number}'


class UserBeneficiaries(AuditableModel):
    app_ref = models.CharField(max_length=255, null=True, blank=True)
    f_name = models.CharField(max_length=255, null=True, blank=True)
    l_name = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=False, blank=False)
    account_number = models.CharField(max_length=255, null=False, blank=False)
    routing_number = models.CharField(max_length=255, null=True, blank=True)
    swift_code = models.CharField(max_length=255, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    bank_branch = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'Beneficiary for {self.user.email or self.user.mobile or self.user.telephone} \
            is {self.f_name} with account {self.account_number}'


class AgentVesselOwnerRelationship(AuditableModel):
    # This import here prevent circular import issues
    from common.utils import generate_uuid
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('terminated', 'Terminated'),
    ]

    app_ref = models.CharField(max_length=50, default=generate_uuid, unique=True)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vessel_owner_relationships')
    vessel_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agent_relationships')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')

    class Meta:
        unique_together = ('agent', 'vessel_owner')

    def __str__(self):
        return f'Agent: {self.agent.first_name} {self.agent.last_name} ({self.agent.email or self.agent.mobile}) - ' \
               f'Vessel Owner: {self.vessel_owner.first_name} {self.vessel_owner.last_name} ' \
               f'({self.vessel_owner.email or self.vessel_owner.mobile})'


class TraderVesselOwnerRelationship(AuditableModel):
    trader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trader_vessel_owner_relationships')
    vessel_owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vessel_owner_trader_relationships')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['trader', 'vessel_owner'], name='unique_trader_vessel_owner'),
            models.CheckConstraint(check=~Q(trader=F('vessel_owner')), name='trader_vessel_owner_not_same_user'),
        ]

    def clean(self):
        super().clean()

        if self.trader_id and not self.trader.groups.filter(name='trader').exists():
            raise ValidationError({'trader': 'Selected user must be in the trader group.'})

        if self.vessel_owner_id and not self.vessel_owner.groups.filter(name='vessel_owner').exists():
            raise ValidationError({'vessel_owner': 'Selected user must be in the vessel_owner group.'})

    def __str__(self):
        return f'Trader: {self.trader.first_name} {self.trader.last_name} ({self.trader.email or self.trader.mobile}) - ' \
               f'Vessel Owner: {self.vessel_owner.first_name} {self.vessel_owner.last_name} ' \
               f'({self.vessel_owner.email or self.vessel_owner.mobile})'
