from django import forms
from contracts.models import UserContractAccess, Contract
from accounts.models import User


class ContractAccessForm(forms.ModelForm):
    class Meta:
        model = UserContractAccess
        fields = ['contract', 'user']

        widgets = {
            'contract': forms.Select(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'user': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

        self.fields['contract'].queryset = Contract.objects.all() if self.request.user.is_superuser \
            else Contract.objects.filter(created_by=self.request.user.id)
        self.fields['user'].queryset = User.objects.all() if not self.request.user.is_superuser \
            else User.objects.filter(created_by=self.request.user.id)
