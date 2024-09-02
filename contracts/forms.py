from django import forms
from contracts.models import UserContractAccess
from accounts.models import User

class ContractAccessForm(forms.ModelForm):
    class Meta:
        model = UserContractAccess
        fields = ['contract', 'user']

        widgets = {
            'contract': forms.Select(attrs={
                'class': 'form-control',
                'readonly': True,
                'disabled': True
            }),
            'user': forms.Select(attrs={'class': 'form-control'})
        }

    
