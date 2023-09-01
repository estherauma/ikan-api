from django import forms

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
