
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from accounts.models import User


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
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'placeholder': 'Enter your email'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password1',
            'placeholder': 'Enter your password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password2',
            'placeholder': 'Confirm your password'
        })
    )
    # TODO: add profile image field

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'password1', 'password2', 'first_name', 'last_name', 'profile_image')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(self.auth_common_text.get('emailAlreadyExists', 'Email already exists.'))
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError(self.auth_common_text.get('passwordsDoNotMatch', 'Passwords do not match.'))
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
            self.fields['email'].widget.attrs['placeholder'] = auth_common_text.get('enterYourEmail',
                                                                                    'Enter your email')
            self.fields['password1'].widget.attrs['placeholder'] = auth_common_text.get('enterYourPassword',
                                                                                        'Enter your password')
            self.fields['password2'].widget.attrs['placeholder'] = auth_common_text.get('confirmYourPassword',
                                                                                        'Confirm your password')
            self.fields['email'].label = auth_common_text.get('email', 'Email')
            self.fields['first_name'].label = auth_common_text.get('firstName', 'First Name')
            self.fields['last_name'].label = auth_common_text.get('lastName', 'Last Name')
            self.fields['password1'].label = auth_common_text.get('password', 'Password')
            self.fields['password2'].label = auth_common_text.get('confirmPassword', 'Confirm Password')


class RequestPasswordResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'placeholder': 'Enter your email'
        })
    )

    def __init__(self, *args, **kwargs):
        auth_common_text = kwargs.pop('auth_common_text', {})
        super().__init__(*args, **kwargs)
        if auth_common_text:
            self.fields['email'].widget.attrs['placeholder'] = auth_common_text.get('enterYourEmail',
                                                                                    'Enter your email')
            self.fields['email'].label = auth_common_text.get('email', 'Email')


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'email',
            'placeholder': 'Enter your email'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'password1',
            'placeholder': 'Enter your new password'
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
        max_length=5,
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError(self.auth_common_text.get('userDoesNotExist', 'User does not exist.'))
        return email

    def clean_reset_password_token(self):
        email = self.cleaned_data.get('email')
        reset_password_token = self.cleaned_data.get('reset_password_token')
        if not User.objects.filter(email=email, reset_password_token=reset_password_token).exists():
            raise forms.ValidationError(self.auth_common_text.get('invalidResetPasswordToken',
                                                                  'Invalid reset password token.'))
        return reset_password_token

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError(self.auth_common_text.get('passwordsDoNotMatch', 'Passwords do not match.'))
        return password2

    def __init__(self, *args, **kwargs):
        auth_common_text = kwargs.pop('auth_common_text', {})
        self.auth_common_text = auth_common_text
        super().__init__(*args, **kwargs)
        if auth_common_text:
            self.fields['email'].widget.attrs['placeholder'] = auth_common_text.get('enterYourEmail',
                                                                                    'Enter your email')
            self.fields['password1'].widget.attrs['placeholder'] = auth_common_text.get('enterYourNewPassword',
                                                                                        'Enter your new password')
            self.fields['password2'].widget.attrs['placeholder'] = auth_common_text.get('confirmYourPassword',
                                                                                        'Confirm your password')
            self.fields['reset_password_token'].widget.attrs['placeholder'] = auth_common_text.get(
                'enterYourPasswordResetToken', 'Enter your password reset token')
            self.fields['email'].label = auth_common_text.get('email', 'Email')
            self.fields['password1'].label = auth_common_text.get('newPassword', 'New Password')
            self.fields['password2'].label = auth_common_text.get('confirmPassword', 'Confirm Password')
            self.fields['reset_password_token'].label = auth_common_text.get('resetPasswordToken',
                                                                             'Reset Password Token')


class InviteUser(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control mb-3',
            'id': 'email',
            'placeholder': 'Enter your email'
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
            self.fields['email'].widget.attrs['placeholder'] = auth_common_text.get('enterYourEmail',
                                                                                    'Enter your email')
            self.fields['first_name'].widget.attrs['placeholder'] = auth_common_text.get(
                'enterYourFirstName', 'Enter your first name') + f' ({auth_common_text.get("optional", "Optional")})'
            self.fields['last_name'].widget.attrs['placeholder'] = auth_common_text.get(
                'enterYourLastName', 'Enter your last name') + f' ({auth_common_text.get("optional", "Optional")})'
            self.fields['email'].label = auth_common_text.get('email', 'Email')
            self.fields['first_name'].label = auth_common_text.get('firstName', 'First Name')
            self.fields['last_name'].label = auth_common_text.get('lastName', 'Last Name')
            self.fields['role'].label = auth_common_text.get('role', 'Role')


class ResendTokenForm(forms.Form):
    email = forms.EmailField(widget=forms.HiddenInput())


class LoginForm(forms.Form):
    email_or_phone = forms.CharField(
        label='Email or Phone Number',
        widget=forms.TextInput(attrs={'placeholder': 'Enter email or phone number', 'class': 'form-control'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", 'placeholder': 'Enter your password', 'class': 'form-control'})
    )


class CreateWorkerForVOForm(forms.Form):
    """
    Form to create a worker for a vessel owner.
    This is a superuser feature to create workers for VOs so the
    worker would appear in the VO's dashboard
    """
    vessel_owner = forms.ModelChoiceField(
        # queryset=User.objects.User.objects.none()
        queryset=User.objects.filter(groups__name='vessel_owner'),
        widget=forms.Select(attrs={'class': 'form-control ikan-select'}),
        help_text="Select a vessel owner to attach to this worker."
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control mb-3',
            'id': 'email',
            'placeholder': 'Enter worker email',
            'autocomplete': 'off'
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

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 != password2:
            raise forms.ValidationError(self.auth_common_text.get('passwordsDoNotMatch', 'Passwords do not match.'))
        return password2

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        auth_common_text = kwargs.pop('auth_common_text', {})
        self.auth_common_text = auth_common_text
        super(CreateWorkerForVOForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['autocomplete'] = 'off'
            pass
        if user:
            self.fields['vessel_owner'].queryset = User.objects.filter(
                groups__name='vessel_owner'
            ).exclude(id=user.id)
