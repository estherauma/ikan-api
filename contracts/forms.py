from django import forms
from contracts.models import UserContractAccess, Contract
from accounts.models import User
from companies.models import Company


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


class AddContractForm(forms.ModelForm):
    taiwanese_company = forms.ChoiceField(
        required=False, widget=forms.Select(attrs={'class': 'form-control ikan-select'}))
    indonesian_company = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control ikan-select'})
    )
    indonesian_company = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control ikan-select'})
    )
    contract_signature = forms.FileField(required=True, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Contract
        fields = ['name', 'start_date', 'end_date', 'description', 'taiwanese_company', 'indonesian_company', 'kind', ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'kind': forms.Select(
                choices=[('', 'Select Contract Type'), ('company', 'Company'), ('worker', 'Worker')],
                attrs={'class': 'form-control ikan-select'}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            # TODO: change default select option to gray and not selectable
            taiwan_choices = [('', 'Select Taiwanese Company')]
            taiwan_companies = Company.objects.filter(country='Taiwan', created_by=user.id)
            if taiwan_companies.exists():
                taiwan_choices += [(company.id, company.name) for company in taiwan_companies]
            self.fields['taiwanese_company'].choices = taiwan_choices

            indonesian_choices = [('', 'Select Indonesian Company')]
            indonesian_companies = Company.objects.filter(country='Indonesia', created_by=user.id)
            if indonesian_companies.exists():
                indonesian_choices += [(company.id, company.name) for company in indonesian_companies]
            self.fields['indonesian_company'].choices = indonesian_choices

            # Make the file field optional when updating
            if self.instance and self.instance.pk and self.instance.contract_document.exists():
                self.fields['contract_signature'].required = False
