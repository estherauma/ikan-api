
import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import Group
from accounts.models import User, AgentVesselOwnerRelationship
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from common.twilio import check_verification_code


def validate_email_or_phone(value, auth_common_text=None):
    value = value.strip()
    is_email = False
    is_phone = False

    # Email validation
    try:
        validate_email(value)
        is_email = True
    except ValidationError:
        pass

    # Phone number validation
    phone_pattern = r"^\+?\d{9,15}$"
    if re.match(phone_pattern, value):
        is_phone = True

    if not is_email and not is_phone:
        raise forms.ValidationError(auth_common_text.get('enterValidEmailOrPhoneNumber',
                                                         'Enter a valid email address or phone number.'))

    return {
        'value': value,
        'is_email': is_email,
        'is_phone': is_phone
    }


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'first_name',
            'placeholder': 'Enter your first name (Optional)'
        }),
        max_length=30,
        required=False,
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'last_name',
            'placeholder': 'Enter your last name (Optional)'
        }),
        max_length=30,
        required=False,
    )
    email_or_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control ikan-phonenumber-input',
            'id': 'email_or_phone',
            'placeholder': 'Enter your email or phone number',
            'autocomplete': 'off'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password1',
            'placeholder': 'Enter your password',
            'autocomplete': 'new-password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password2',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        })
    )
    # TODO: add profile image field

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email_or_phone', 'password1', 'password2', 'first_name', 'last_name', 'profile_image')

    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone').strip()
        is_email = False
        is_phone = False

        # Email validation
        try:
            validate_email(email_or_phone)
            is_email = True
        except ValidationError:
            pass

        # Phone number validation
        phone_pattern = r"^\+?\d{9,15}$"
        if re.match(phone_pattern, email_or_phone):
            is_phone = True

        if not is_email and not is_phone:
            raise forms.ValidationError(self.auth_common_text.get('enterValidEmailOrPhoneNumber',
                                                                  'Enter a valid email address or phone number.'))

        if is_email:
            if User.objects.filter(email=email_or_phone).exists():
                raise forms.ValidationError(self.auth_common_text.get('emailAlreadyExists', 'Email already exists.'))
            # add email to cleaned data for use in the view
            self.cleaned_data['email'] = email_or_phone
        else:
            if User.objects.filter(Q(mobile=email_or_phone) | Q(telephone=email_or_phone)).exists():
                raise forms.ValidationError(self.auth_common_text.get('phoneNumberAlreadyExists',
                                                                      'Phone number already exists.'))
            # add phone number to cleaned data for use in the view
            self.cleaned_data['mobile'] = email_or_phone

        # Add flags to cleaned data to indicate whether email or phone number was provided
        self.cleaned_data['has_email'] = is_email
        self.cleaned_data['has_phone_number'] = is_phone

        return email_or_phone

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError(self.auth_common_text.get('passwordsDoNotMatch', 'Passwords do not match.'))

        try:
            validate_password(password2, self.instance)
        except ValidationError as error:
            raise forms.ValidationError(error.messages)

        return password2

    def __init__(self, *args, **kwargs):
        auth_common_text = kwargs.pop('auth_common_text', {})
        self.auth_common_text = auth_common_text
        super().__init__(*args, **kwargs)
        if auth_common_text:
            self.fields['first_name'].widget.attrs['placeholder'] = auth_common_text.get(
                'enterYourFirstName', 'Enter your first name') + f' ({auth_common_text.get("optional", "Optional")})'
            self.fields['last_name'].widget.attrs['placeholder'] = auth_common_text.get(
                'enterYourLastName', 'Enter your last name') + f' ({auth_common_text.get("optional", "Optional")})'
            self.fields['email_or_phone'].widget.attrs['placeholder'] = \
                auth_common_text.get('enterYourEmailOrPhoneNumber', 'Enter your email or phone number')
            self.fields['password1'].widget.attrs['placeholder'] = auth_common_text.get('enterYourPassword',
                                                                                        'Enter your password')
            self.fields['password2'].widget.attrs['placeholder'] = auth_common_text.get('confirmYourPassword',
                                                                                        'Confirm your password')
            self.fields['email_or_phone'].label = auth_common_text.get('emailOrPhoneNumber', 'Email or Phone Number')
            self.fields['first_name'].label = auth_common_text.get('firstName', 'First Name')
            self.fields['last_name'].label = auth_common_text.get('lastName', 'Last Name')
            self.fields['password1'].label = auth_common_text.get('password', 'Password')
            self.fields['password2'].label = auth_common_text.get('confirmPassword', 'Confirm Password')


class RequestPasswordResetForm(forms.Form):
    email_or_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control ikan-phonenumber-input',
            'id': 'email_or_phone',
            'placeholder': 'Enter your email or phone number'
        })
    )

    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone').strip()
        validation_result = validate_email_or_phone(email_or_phone, self.auth_common_text)

        if validation_result['is_email']:
            self.cleaned_data['email'] = email_or_phone
        if validation_result['is_phone']:
            self.cleaned_data['mobile'] = email_or_phone

        self.cleaned_data['has_phone_number'] = validation_result['is_phone']
        self.cleaned_data['has_email'] = validation_result['is_email']
        return email_or_phone

    def __init__(self, *args, **kwargs):
        auth_common_text = kwargs.pop('auth_common_text', {})
        self.auth_common_text = auth_common_text
        super().__init__(*args, **kwargs)
        if auth_common_text:
            self.fields['email_or_phone'].widget.attrs['placeholder'] = \
                auth_common_text.get('enterYourEmailOrPhoneNumber',
                                     'Enter your email or phone number')
            self.fields['email_or_phone'].label = auth_common_text.get('emailOrPhoneNumber', 'Email or Phone Number')


class PasswordResetForm(forms.Form):
    email_or_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control ikan-phonenumber-input',
            'id': 'email_or_phone',
            'placeholder': 'Enter your email or phone number'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password1',
            'placeholder': 'Enter your new password',
            'autocomplete': 'new-password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password2',
            'placeholder': 'Confirm your password'
        })
    )
    reset_password_token = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'reset_password_token',
            'placeholder': 'Enter your password reset token'
        }),
        max_length=6,
    )

    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone')

        validation_result = validate_email_or_phone(email_or_phone, self.auth_common_text)
        if validation_result['is_email']:
            self.cleaned_data['email'] = email_or_phone
        if validation_result['is_phone']:
            self.cleaned_data['mobile'] = email_or_phone
        self.cleaned_data['has_phone_number'] = validation_result['is_phone']
        self.cleaned_data['has_email'] = validation_result['is_email']

        user_queryset = User.objects.none()
        if self.cleaned_data.get('has_email'):
            user_queryset = User.objects.filter(email=email_or_phone)
        if self.cleaned_data.get('has_phone_number'):
            user_queryset = User.objects.filter(Q(mobile=email_or_phone) | Q(telephone=email_or_phone))
        if not user_queryset.exists():
            raise forms.ValidationError(self.auth_common_text.get('userDoesNotExist', 'User does not exist.'))
        return email_or_phone

    def clean_reset_password_token(self):
        email_or_phone = self.cleaned_data.get('email_or_phone')
        reset_password_token = self.cleaned_data.get('reset_password_token')

        email_or_phone_validation_result = validate_email_or_phone(email_or_phone)
        query = Q()
        if email_or_phone_validation_result['is_email']:
            query |= Q(email=email_or_phone)
        if email_or_phone_validation_result['is_phone']:
            query |= Q(mobile=email_or_phone) | Q(telephone=email_or_phone)

        if not query:
            raise forms.ValidationError(self.auth_common_text.get('enterValidEmailOrPhoneNumber',
                                                                  'Enter a valid email address or phone number.'))
        user_queryset = User.objects.filter(
            query,
            reset_password_token=reset_password_token
        )
        if (self.cleaned_data.get('has_phone_number') and
            not check_verification_code(self.request, email_or_phone, reset_password_token, self.auth_common_text)) or \
                (self.cleaned_data.get('has_email') and not user_queryset.exists()):
            raise forms.ValidationError(self.auth_common_text.get('invalidResetPasswordToken',
                                                                  'Invalid reset password token.'))
        return reset_password_token

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError(self.auth_common_text.get('passwordsDoNotMatch', 'Passwords do not match.'))

        user = None
        if self.cleaned_data.get('has_email'):
            user = User.objects.filter(email=self.cleaned_data.get('email')).first()
        elif self.cleaned_data.get('has_phone_number'):
            mobile = self.cleaned_data.get('mobile')
            user = User.objects.filter(Q(mobile=mobile) | Q(telephone=mobile)).first()

        try:
            validate_password(password2, user)
        except ValidationError as error:
            raise forms.ValidationError(error.messages)

        return password2

    def __init__(self, *args, **kwargs):
        auth_common_text = kwargs.pop('auth_common_text', {})
        request = kwargs.pop('request', None)
        self.auth_common_text = auth_common_text
        self.request = request
        super().__init__(*args, **kwargs)
        if auth_common_text:
            self.fields['email_or_phone'].widget.attrs['placeholder'] = \
                auth_common_text.get('enterYourEmailOrPhoneNumber', 'Enter your email or phone number')
            self.fields['password1'].widget.attrs['placeholder'] = auth_common_text.get('enterYourNewPassword',
                                                                                        'Enter your new password')
            self.fields['password2'].widget.attrs['placeholder'] = auth_common_text.get('confirmYourPassword',
                                                                                        'Confirm your password')
            self.fields['reset_password_token'].widget.attrs['placeholder'] = auth_common_text.get(
                'enterYourPasswordResetToken', 'Enter your password reset token')
            self.fields['email_or_phone'].label = auth_common_text.get('emailOrPhoneNumber', 'Email or Phone Number')
            self.fields['password1'].label = auth_common_text.get('newPassword', 'New Password')
            self.fields['password2'].label = auth_common_text.get('confirmPassword', 'Confirm Password')
            self.fields['reset_password_token'].label = auth_common_text.get('resetPasswordToken',
                                                                             'Reset Password Token')


class InviteUser(forms.Form):
    email_or_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3 ikan-phonenumber-input',
            'id': 'email_or_phone',
            'placeholder': 'Enter your email or phone number'
        }),
        required=True
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'id': 'first_name',
            'placeholder': 'Enter your first name (Optional)'
        }),
        max_length=30,
        required=False,
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'id': 'last_name',
            'placeholder': 'Enter your last name (Optional)'
        }),
        max_length=30,
        required=False,
    )

    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone').strip()
        is_email = False
        is_phone = False

        # Email validation
        try:
            validate_email(email_or_phone)
            is_email = True
        except ValidationError:
            pass

        # Phone number validation
        phone_pattern = r"^\+?\d{9,15}$"
        if re.match(phone_pattern, email_or_phone):
            is_phone = True

        if not is_email and not is_phone:
            raise forms.ValidationError(self.auth_common_text.get('enterValidEmailOrPhoneNumber',
                                                                  'Enter a valid email address or phone number.'))

        if is_email:
            if User.objects.filter(email=email_or_phone).exists():
                # check is user is inactive then resend token
                user = User.objects.get(email=email_or_phone)
                if not user.is_active:
                    raise forms.ValidationError(self.auth_common_text.get('resendInviteToken',
                                                                          'User already exists. \
                                                                            Please resend invite token.'))
                raise forms.ValidationError(self.auth_common_text.get('userWithEmailAlreadyExists',
                                                                      'User with this email address already exists.'))
            # add email to cleaned data for use in the view
            self.cleaned_data['email'] = email_or_phone
        else:
            if User.objects.filter(Q(mobile=email_or_phone) | Q(telephone=email_or_phone)).exists():
                raise forms.ValidationError(self.auth_common_text.get('userWithPhoneNumberAlreadyExists',
                                                                      'User with this phone number already exists.'))
            # add phone number to cleaned data for use in the view
            self.cleaned_data['mobile'] = email_or_phone

        # Add flags to cleaned data to indicate whether email or phone number was provided
        self.cleaned_data['has_email'] = is_email
        self.cleaned_data['has_phone_number'] = is_phone

        return email_or_phone

    def __init__(self, *args, **kwargs):
        auth_common_text = kwargs.pop('auth_common_text', {})
        self.auth_common_text = auth_common_text
        super(InviteUser, self).__init__(*args, **kwargs)
        group_choices = [(group.name, group.name) for group in Group.objects.all()]
        select_role_text = f'-- {auth_common_text.get("selectARole", "Select a role")} --'
        group_choices.insert(0, ('', select_role_text))

        self.fields['role'] = forms.ChoiceField(
            choices=group_choices,
            widget=forms.Select(attrs={
                'class': 'form-control mb-3',
                'id': 'role',
            }),
            required=True
        )

        if auth_common_text:
            self.fields['email_or_phone'].widget.attrs['placeholder'] = \
                auth_common_text.get('enterYourEmailOrPhoneNumber', 'Enter your email or phone number')
            self.fields['first_name'].widget.attrs['placeholder'] = auth_common_text.get(
                'enterYourFirstName', 'Enter your first name') + f' ({auth_common_text.get("optional", "Optional")})'
            self.fields['last_name'].widget.attrs['placeholder'] = auth_common_text.get(
                'enterYourLastName', 'Enter your last name') + f' ({auth_common_text.get("optional", "Optional")})'
            self.fields['email_or_phone'].label = auth_common_text.get('emailOrPhoneNumber', 'Email or Phone Number')
            self.fields['first_name'].label = auth_common_text.get('firstName', 'First Name')
            self.fields['last_name'].label = auth_common_text.get('lastName', 'Last Name')
            self.fields['role'].label = auth_common_text.get('role', 'Role')


class ResendTokenForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput(), required=False)
    mobile = forms.CharField(widget=forms.HiddenInput(), required=False)


class LoginForm(forms.Form):
    email_or_phone = forms.CharField(
        label='Email or Phone Number',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter email or phone number',
                'class': 'form-control ikan-phonenumber-input'
            }
        )
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                'placeholder': 'Enter your password',
                'class': 'form-control'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        auth_common_text = kwargs.pop('auth_common_text', {})
        super(LoginForm, self).__init__(*args, **kwargs)
        if auth_common_text:
            self.fields['email_or_phone'].widget.attrs['placeholder'] = \
                auth_common_text.get('enterYourEmailOrPhoneNumber', 'Enter your email address or phone number')
            self.fields['password'].widget.attrs['placeholder'] = auth_common_text.get('enterYourPassword',
                                                                                       'Enter your password')
            self.fields['email_or_phone'].label = auth_common_text.get('emailOrPhoneNumber', 'Email or Phone Number')
            self.fields['password'].label = auth_common_text.get('password', 'Password')


class CreateWorkerForVOForm(forms.Form):
    """
    Form to create a worker for a vessel owner.
    This is a superuser feature to create workers for VOs so the
    worker would appear in the VO's dashboard
    """
    vessel_owner = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='vessel_owner'),
        widget=forms.Select(attrs={'class': 'form-control ikan-select'}),
        help_text="Select a vessel owner to attach to this worker.",
        required=True
    )
    email_or_phone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3 ikan-phonenumber-input',
            'id': 'email_or_phone',
            'placeholder': 'Enter your email or phone number'
        }),
        required=True
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'id': 'first_name',
            'placeholder': 'Enter worker first name (Optional)',
            'autocomplete': 'off'
        }),
        max_length=30,
        required=False,
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'id': 'last_name',
            'placeholder': 'Enter worker last name (Optional)',
            'autocomplete': 'off'
        }),
        max_length=30,
        required=False,
    )
    password1 = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'password1',
            'placeholder': 'Enter worker password',
            'autocomplete': 'off'
        })
    )
    password2 = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'password2',
            'placeholder': 'Confirm worker password',
            'autocomplete': 'off'
        })
    )

    def clean_email_or_phone(self):
        email_or_phone = self.cleaned_data.get('email_or_phone').strip()
        validation_result = validate_email_or_phone(email_or_phone, self.auth_common_text)
        query = Q()

        if validation_result['is_email']:
            self.cleaned_data['email'] = email_or_phone
            query |= Q(email=email_or_phone)
        if validation_result['is_phone']:
            self.cleaned_data['mobile'] = email_or_phone
            query |= Q(mobile=email_or_phone) | Q(telephone=email_or_phone)

        self.cleaned_data['has_phone_number'] = validation_result['is_phone']
        self.cleaned_data['has_email'] = validation_result['is_email']

        user_queryset = User.objects.filter(query)
        if not query:
            user_queryset = User.objects.none()
        if user_queryset.exists():
            raise forms.ValidationError(
                self.auth_common_text.get('userWithEmailOrPhoneAlreadyExists',
                                          'User with this email or phone number already exists.'))
        return email_or_phone

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError(self.auth_common_text.get('passwordsDoNotMatch', 'Passwords do not match.'))

        try:
            validate_password(password2)
        except ValidationError as error:
            raise forms.ValidationError(error.messages)

        return password2

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        auth_common_text = kwargs.pop('auth_common_text', {})
        self.auth_common_text = auth_common_text
        super(CreateWorkerForVOForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['autocomplete'] = 'off'

        if user:
            self.fields['vessel_owner'].queryset = User.objects.filter(
                groups__name='vessel_owner'
            ).exclude(id=user.id)
            # if user is an agent, return only vessel owners that are attached to the agent
            if user.groups.filter(name__in=['taiwanese_agent', 'indonesian_agent']).exists():
                self.fields['vessel_owner'].queryset = user.vessel_owners


class CreateAgentVesselownerRelationshipForm(forms.Form):
    agent = forms.ModelChoiceField(
        queryset=User.objects.filter(Q(groups__name='taiwanese_agent') | Q(groups__name='indonesian_agent')),
        widget=forms.Select(attrs={'class': 'form-control ikan-select'}),
        help_text="Select an agent to attach to this vessel owner.",
        required=True
    )
    vessel_owner = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='vessel_owner'),
        widget=forms.Select(attrs={'class': 'form-control ikan-select'}),
        help_text="Select a vessel owner to attach to this agent.",
        required=True
    )
    status = forms.ChoiceField(
        choices=[('active', 'Active'), ('pending', 'Pending'), ('terminated', 'Terminated')],
        widget=forms.Select(attrs={'class': 'form-control ikan-select'}),
        help_text="Select the status of the relationship.",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        agent = cleaned_data.get('agent')
        vessel_owner = cleaned_data.get('vessel_owner')

        if agent and vessel_owner:
            if AgentVesselOwnerRelationship.objects.filter(agent=agent, vessel_owner=vessel_owner).exists():
                raise forms.ValidationError(
                    "This agent and vessel owner relationship already exists."
                )
            if agent == vessel_owner:
                raise forms.ValidationError(
                    "Agent and vessel owner cannot be the same user."
                )
        return cleaned_data
