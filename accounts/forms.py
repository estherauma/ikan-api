
from django import forms
from django.contrib.auth.forms import UserCreationForm

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
            raise forms.ValidationError('Email already exists.')
        return email

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