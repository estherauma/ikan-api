from django import forms
from vessels.models import Vessel
from payments.models import Payment
from accounts.models import User
from django.db.models import Q
from django.forms import modelformset_factory, BaseModelFormSet
from payments.utils import payment_categories, payment_methods, payment_currencies


class UploadPaymentsForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "id": "file",
                "accept": ".xlsx, .xls",
            }
        ),
        label="",
    )


class VesselSelectForm(forms.Form):
    vessel = forms.ModelChoiceField(
        queryset=Vessel.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                "placeholder": "Select Vessel",
                "style": "min-height: 45px; border-radius: 10px; border-width: 1px; min-width: 300px;\
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


class AddPaymentsForm(forms.ModelForm):
    payment_category = forms.ChoiceField()
    payment_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        )
    )
    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        )
    )
    end_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        )
    )
    payment_method = forms.ChoiceField()
    cash_currency = forms.ChoiceField()
    bank_transfer_currency = forms.ChoiceField()

    class Meta:
        model = Payment
        # We are listing the fields instead of using exclude
        # to control their order in the row when displaying
        fields = [
            "user",
            "payment_date",
            "payment_category",
            "beneficiary_name",
            "start_date",
            "end_date",
            "duration",
            "total_usd_amount_received",
            "payment_method",
            "cash_usd_amount",
            "cash_currency",
            "cash_local_amount",
            "cash_exchange_rate",
            "is_cash_beneficiary_crew",
            "cash_beneficiary_relationship",
            "cash_beneficiary_contact",
            "cash_beneficiary_contact_platform",
            "bank_transfer_usd_amount",
            "bank_transfer_currency",
            "bank_transfer_local_amount",
            "bank_transfer_exchange_rate",
            "is_bank_transfer_beneficiary_crew",
            "bank_account_name",
            "bank_account_number",
            "bank_name",
            "bank_transfer_beneficiary_relationship",
            "bank_transfer_beneficiary_contact",
            "bank_transfer_beneficiary_contact_platform",
            "has_deductions",
        ]

    def __init__(self, *args, vessel=None, loggedin_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        empty_select_choice = [("", "")]

        for field in self.fields:
            self.fields[field].widget.attrs[
                "style"
            ] = "min-height: 45px; border-radius: 10px; border-width: 1px; min-width: 200px;\
                max-width: 300px;padding: 0 10px; font-size: 1rem;"

        self.fields["payment_category"].choices = empty_select_choice + [
            (item["key"], item["value"]) for item in payment_categories
        ]
        self.fields["payment_method"].choices = empty_select_choice + [
            (item["key"], item["value"]) for item in payment_methods
        ]
        self.fields["cash_currency"].choices = empty_select_choice + [
            (item["key"], item["value"]) for item in payment_currencies
        ]
        self.fields["bank_transfer_currency"].choices = empty_select_choice + [
            (item["key"], item["value"]) for item in payment_currencies
        ]

        if vessel and loggedin_user:
            # TODO: change query to display workers attached to selected vessel
            # display worker names only
            vessel_workers = User.objects.filter(
                Q(created_by=loggedin_user.id) & Q(groups__name="worker")
            ).distinct()

            self.extra_forms = len(vessel_workers) + 1
            self.fields["user"].queryset = vessel_workers


class BasePaymentFormSet(BaseModelFormSet):
    def __init__(self, *args, vessel=None, loggedin_user=None, **kwargs):
        self.vessel = vessel
        self.loggedin_user = loggedin_user
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs["vessel"] = self.vessel
        kwargs["loggedin_user"] = self.loggedin_user
        return super()._construct_form(i, **kwargs)


PaymentsFormSet = modelformset_factory(
    Payment, form=AddPaymentsForm, formset=BasePaymentFormSet, extra=3
)
