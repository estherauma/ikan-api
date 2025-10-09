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
    kind = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-control ikan-select'})
    )
    upload_contract = forms.FileField(required=True, widget=forms.FileInput(attrs={'class': 'form-control'}))

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
        labels = kwargs.pop("form_labels", {})
        super().__init__(*args, **kwargs)
        if user:
            select_option_text = labels.get('select_option', 'Select option')
            worker_text = labels.get('worker', 'Worker')
            company_text = labels.get('company', 'Company')
            taiwan_choices = [('', select_option_text)]
            taiwan_companies = Company.objects.filter(country='Taiwan', created_by=user.id)
            if taiwan_companies.exists():
                taiwan_choices += [(company.id, company.name) for company in taiwan_companies]
            self.fields['taiwanese_company'].choices = taiwan_choices

            indonesian_choices = [('', select_option_text)]
            indonesian_companies = Company.objects.filter(country='Indonesia', created_by=user.id)
            if indonesian_companies.exists():
                indonesian_choices += [(company.id, company.name) for company in indonesian_companies]
            self.fields['indonesian_company'].choices = indonesian_choices

            self.fields['kind'].choices = [('', select_option_text), ('company', company_text), ('worker', worker_text)]

            # Make the upload_contract field optional when updating and it has a value
            if self.instance and self.instance.pk and self.instance.contract_document.exists():
                self.fields['upload_contract'].required = False

        if labels:
            for field_name, field in self.fields.items():
                if field_name in labels:
                    field.label = labels[field_name]


class CreateContractForVOForm(forms.Form):
    """
    Form for attaching VO to contract & selecting a worker to grant contract access.
    This is a superuser feature to create contracts for VOs so the
    contract would appear in the VO's dashboard.
    """
    vessel_owner = forms.ModelChoiceField(
        # queryset=User.objects.User.objects.none()
        queryset=User.objects.filter(groups__name='vessel_owner'),
        widget=forms.Select(attrs={'class': 'form-control ikan-select'}),
        help_text="Select a vessel owner to attach to this contract."
    )
    worker = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='worker'),
        widget=forms.Select(attrs={'class': 'form-control ikan-select'}),
        required=False,
        help_text="Select a worker to grant contract access."
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['vessel_owner'].queryset = User.objects.filter(
                groups__name='vessel_owner'
            ).exclude(id=user.id)

        # TODO: Fix filter workers based on selected vessel owner
        if 'vessel_owner' in self.data:
            vessel_owner_id = self.data.get('vessel_owner').id
            self.fields['worker'].queryset = User.objects.filter(
                groups__name='worker', created_by=vessel_owner_id
            ).exclude(id=vessel_owner_id)
        elif self.initial.get('vessel_owner'):
            vessel_owner_id = self.initial.get('vessel_owner').id
            self.fields['worker'].queryset = User.objects.filter(
                groups__name='worker', created_by=vessel_owner_id
            ).exclude(id=vessel_owner_id)
        else:
            self.fields['worker'].queryset = User.objects.filter(groups__name='worker')
            # self.fields['worker'].queryset = User.objects.none()
