from django import forms
from vessels.models import Vessel
from wages.models import Wage
from django.forms import modelformset_factory, BaseModelFormSet
from django.core.exceptions import ValidationError
from wages.utils import (
    wage_fields,
    get_workers_on_vessel,
)


class VesselSelectForm(forms.Form):
    vessel = forms.ModelChoiceField(
        queryset=Vessel.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                "placeholder": "Select Vessel",
                "style": "min-height: 45px; border-radius: 10px; border-width: 1px; min-width: 200px;\
                    max-width: 500px; padding: 0 10px; font-size: 1.1rem;",
                "id": "vessel-select",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["vessel"].queryset = Vessel.objects.filter(created_by=user.id)


class AddWageForm(forms.ModelForm):
    beneficiary_relationship = forms.ChoiceField()

    class Meta:
        model = Wage
        fields = wage_fields
        widgets = {
            "vessel": forms.Select(
                attrs={
                    "class": "form-select",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                }
            ),
            "user": forms.Select(
                attrs={
                    "class": "form-select",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                }
            ),
            "payment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                }
            ),
            "usd_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                    "step": "0.01", 
                    "min": "0",
                    "placeholder": "0.00",
                }
            ),
            "payslip": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                    "accept": ".pdf,.jpg,.jpeg,.png",
                    "placeholder": "Upload payslip (PDF, JPG, PNG)",
                    "id": "payslip-upload",
                }
            ),
            "crew_bank_transfer_receipt": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                    "accept": ".pdf,.jpg,.jpeg,.png",
                    "placeholder": "Upload crew bank transfer receipt (PDF, JPG, PNG)",
                    "id": "crew-bank-transfer-receipt-upload",
                }
            ),
            "beneficiary_bank_transfer_receipt": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                    "accept": ".pdf,.jpg,.jpeg,.png",
                    "placeholder": "Upload beneficiary bank transfer receipt (PDF, JPG, PNG)",
                    "id": "beneficiary-bank-transfer-receipt-upload",
                }
            ),
            "beneficiary_relationship": forms.Select(
                attrs={
                    "class": "form-select",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",    
                }
            ),
            "beneficiary_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                    "placeholder": "Enter beneficiary name",    
                    "id": "beneficiary-name",
                }
            ),
            "beneficiary_contact": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                    "placeholder": "Enter beneficiary contact",
                    "id": "beneficiary-contact",
                }
            ),
            "beneficiary_contact_platform": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "style": "min-height: 45px; border-radius: 10px; border-width: 1px; padding: 0 10px;\
                        font-size: 1.1rem;",
                    "placeholder": "Enter beneficiary contact platform (e.g., WhatsApp, Email)",
                    "id": "beneficiary-contact-platform",
                }
            ),
        }
        labels = {
            "usd_amount": "Amount (USD)",
            "payslip": "Payslip",
            "crew_bank_transfer_receipt": "Crew Bank Transfer Receipt",
            "beneficiary_bank_transfer_receipt": "Beneficiary Bank Transfer Receipt",
            "beneficiary_relationship": "Beneficiary Relationship",
            "beneficiary_name": "Beneficiary Name",
            "beneficiary_contact": "Beneficiary Contact",
            "beneficiary_contact_platform": "Beneficiary Contact Platform",
        }

    def __init__(self, *args, vessel=None, loggedin_user=None, payments_common_text={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.vessel = vessel
        self.payments_common_text = payments_common_text
        empty_select_choice = [("", "")]
