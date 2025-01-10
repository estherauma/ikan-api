from django import forms
from vessels.models import Vessel
from payments.models import Payment
from accounts.models import User
from django.db.models import Q


class UploadPaymentsForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'file',
            'accept': '.xlsx, .xls',
        }),
        label='',
    )


class VesselSelectForm(forms.Form):
    vessel = forms.ModelChoiceField(
        queryset=Vessel.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                'placeholder': 'Select Vessel',
                'style': 'min-height: 45px; border-radius: 10px; border-width: 1px; min-width: 300px; max-width: 500px; padding: 0 10px; font-size: 1.1rem;',
                'id': 'vessel-select',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['vessel'].queryset = Vessel.objects.filter(created_by=user.id)


class AddPaymentsForm(forms.ModelForm):
    # user = forms.ModelChoiceField(
    #     queryset=User.objects.none(),
    #     # label="Select Vessel",
    #     # required=True
    # )
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'placeholder': 'date'
        })
    )

    class Meta:
        model = Payment
        exclude = ()
        # fields = [
        #     'user',
        #     'payment_date',
        #     'payment_category',
        #     'beneficiary_name'
        #     'start_date'
        #     'end_date'
        #     'duration'
        #     'total_usd_amount_received'
        #     'payment_method'
        #     'cash_usd_amount'
        #     'cash_currency'
        #     'cash_local_amount'
        #     'cash_exchange_rate'
        #     'is_cash_beneficiary_crew'
        #     'cash_beneficiary_relationship'
        #     'cash_beneficiary_contact'
        #     'cash_beneficiary_contact_platform'
        #     'bank_transfer_usd_amount'
        #     'bank_transfer_currency'
        #     'bank_transfer_local_amount'
        #     'bank_transfer_exchange_rate'
        #     'is_bank_transfer_beneficiary_crew'
        #     'bank_account_name'
        #     'bank_account_number'
        #     'bank_name'
        #     'bank_transfer_beneficiary_relationship'
        #     'bank_transfer_beneficiary_contact'
        #     'bank_transfer_beneficiary_contact_platform'
        #     'has_deductions'
        # ]

    def __init__(self, *args, vessel=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["style"] = 'min-height: 45px; border-radius: 10px; border-width: 1px; min-width: 200px; max-width: 300px; padding: 0 10px; font-size: 1rem;'
        
        print('ajjajajaa')
        if vessel:
            print('sdfghj')
            users = User.objects.filter(
                Q(created_by='-Ne7V0lC-YkjfcR6l7I9') &
                Q(groups__name='worker')
            ).distinct()
            print('userssss....', users)

            self.fields['user'].queryset = User.object.filter(created_by='-Ne7V0lC-YkjfcR6l7I9')
            # self.fields['user'].queryset = User.object.all()


PaymentsFormSet = forms.modelformset_factory(Payment, form=AddPaymentsForm, extra=3, exclude=())
