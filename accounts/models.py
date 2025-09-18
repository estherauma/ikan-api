from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from common.models import AuditableModel
from django.utils.translation import gettext_lazy as _
from common.models import BaseModel
from django.core.exceptions import ValidationError
from django.db.models import Q


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """

        if not email:
            raise ValueError('Email field must be set')

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def get_default_user(self):
        default_email = 'default_ikan_user@fiftyeight.io'
        default_password = self.make_random_password()
        try:
            user = self.get(email=default_email)
        except self.model.DoesNotExist:
            user = self.create_user(
                email=default_email,
                password=default_password,
                is_active=False,
            )
        return user


class User(AbstractBaseUser, AuditableModel, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_verified = models.BooleanField(_('verified'), default=False)
    is_staff = models.BooleanField(default=False)
    reset_password_token = models.CharField(null=True, blank=True, max_length=125)
    profile_image = models.URLField(null=True, blank=True)
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

    USERNAME_FIELD = 'email'

    objects = UserManager()

    @property
    def is_admin(self):
        return self.is_superuser

    def __str__(self):
        return f'{self.first_name} {self.last_name} -- {self.email}'

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
            for field, value in numbers.items():
                if existing_users.filter(Q(mobile=value) | Q(telephone=value)).exists():
                    errors[field] = f"{value} is already registered to another user."
            if errors:
                raise ValidationError(errors)


class LoginEvent(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.SET(User.objects.get_default_user), related_name='login_events')
    ip_address = models.GenericIPAddressField()
    date_logged_in = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'login_events'

    def __str__(self) -> str:
        return f'{self.user.email}@{self.ip_address} logged in at {self.date_logged_in}'


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
        return f'Beneficiary for {self.user.email} is {self.f_name} with account {self.account_number}'
