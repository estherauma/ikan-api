from django import forms
from vessels.models import Vessel
from payments.models import Payment
from django.forms import modelformset_factory, BaseModelFormSet
from payments.utils import (
    payment_categories,
    payment_methods,
    payment_currencies,
    payment_fields,
    get_workers_on_vessel,
    payment_beneficiarires,
    cash_fields,
    bank_transfer_fields,
)
from django.core.exceptions import ValidationError


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
    cash_currency = forms.ChoiceField(required=False)
    bank_transfer_currency = forms.ChoiceField(required=False)
    cash_beneficiary_relationship = forms.ChoiceField(required=False)
    bank_transfer_beneficiary_relationship = forms.ChoiceField(required=False)

    class Meta:
        model = Payment
        # We are listing the fields instead of using exclude
        # to control their order in the row when displaying
        fields = payment_fields

    def __init__(self, *args, vessel=None, loggedin_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vessel = vessel
        empty_select_choice = [("", "")]

        # change backgroud color of cash and bank-transfer fields
        # add cash-field class to all cash fields
        # for field in cash_fields:
        #     self.fields[field].widget.attrs["class"] = "cash-field"

        # # add bank-transfer-field class to all bank transfer fields
        # for field in bank_transfer_fields:
        #     self.fields[field].widget.attrs["class"] = "bank-transfer-field"

        for field in self.fields:
            self.fields[field].widget.attrs[
                "style"
            ] = "min-height: 45px; border-radius: 10px; border-width: 1px; min-width: 250px;\
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
        self.fields["cash_beneficiary_relationship"].choices = empty_select_choice + [
            (item["key"], item["value"]) for item in payment_beneficiarires
        ]
        self.fields["bank_transfer_beneficiary_relationship"].choices = empty_select_choice + [
            (item["key"], item["value"]) for item in payment_beneficiarires
        ]

        if vessel:
            workers_on_vessel = get_workers_on_vessel(vessel)
            self.fields["user"].queryset = workers_on_vessel

    def clean_total_usd_amount_received(self):
        total_usd_amount_received = self.cleaned_data.get("total_usd_amount_received")
        if total_usd_amount_received and total_usd_amount_received < 0:
            raise ValidationError("Total USD amount received cannot be negative.")
        return total_usd_amount_received

    def clean_cash_amount(self):
        cash_amount = self.cleaned_data.get("cash_amount")
        if cash_amount and cash_amount < 0:
            raise ValidationError("USD cash amount cannot be negative.")
        return cash_amount

    def clean_cash_exchange_rate(self):
        cash_exchange_rate = self.cleaned_data.get("cash_exchange_rate")
        if cash_exchange_rate and cash_exchange_rate < 0:
            raise ValidationError("Cash exchange rate cannot be negative.")
        return cash_exchange_rate

    def clean_bank_transfer_amount(self):
        bank_transfer_amount = self.cleaned_data.get("bank_transfer_amount")
        if bank_transfer_amount and bank_transfer_amount < 0:
            raise ValidationError("USD bank transfer amount cannot be negative.")
        return bank_transfer_amount

    def clean_bank_transfer_exchange_rate(self):
        bank_transfer_exchange_rate = self.cleaned_data.get(
            "bank_transfer_exchange_rate"
        )
        if bank_transfer_exchange_rate and bank_transfer_exchange_rate < 0:
            raise ValidationError("Bank exchange rate cannot be negative.")
        return bank_transfer_exchange_rate

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        payment_method = cleaned_data.get("payment_method")
        cash_amount = cleaned_data.get("cash_amount")
        cash_currency = cleaned_data.get("cash_currency")
        cash_exchange_rate = cleaned_data.get("cash_exchange_rate")
        cash_beneficiary_name = cleaned_data.get("cash_beneficiary_name")
        cash_beneficiary_relationship = cleaned_data.get(
            "cash_beneficiary_relationship"
        )
        cash_beneficiary_contact = cleaned_data.get("cash_beneficiary_contact")
        bank_transfer_amount = cleaned_data.get("bank_transfer_amount")
        bank_transfer_currency = cleaned_data.get("bank_transfer_currency")
        bank_transfer_exchange_rate = cleaned_data.get("bank_transfer_exchange_rate")
        bank_transfer_beneficiary_name = cleaned_data.get(
            "bank_transfer_beneficiary_name"
        )
        bank_transfer_beneficiary_relationship = cleaned_data.get(
            "bank_transfer_beneficiary_relationship"
        )
        bank_transfer_beneficiary_contact = cleaned_data.get(
            "bank_transfer_beneficiary_contact"
        )
        bank_account_name = cleaned_data.get("bank_account_name")
        bank_account_number = cleaned_data.get("bank_account_number")
        bank_name = cleaned_data.get("bank_name")

        if start_date and end_date:
            if end_date <= start_date:
                self.add_error("end_date", "End date must be greater than start date.")

        # if the paymnet method is either cash or both
        if payment_method != "bank_transfer":
            self.validate_cash_fields(
                cash_currency=cash_currency,
                cash_amount=cash_amount,
                cash_exchange_rate=cash_exchange_rate,
                cash_beneficiary_name=cash_beneficiary_name,
                cash_beneficiary_relationship=cash_beneficiary_relationship,
                cash_beneficiary_contact=cash_beneficiary_contact,
            )
        # if the payment method is either bank_transfer or both
        if payment_method != "cash":
            self.validate_bank_transfer_fields(
                bank_transfer_currency=bank_transfer_currency,
                bank_transfer_amount=bank_transfer_amount,
                bank_transfer_exchange_rate=bank_transfer_exchange_rate,
                bank_transfer_beneficiary_name=bank_transfer_beneficiary_name,
                bank_transfer_beneficiary_relationship=bank_transfer_beneficiary_relationship,
                bank_transfer_beneficiary_contact=bank_transfer_beneficiary_contact,
                bank_name=bank_name,
                bank_account_name=bank_account_name,
                bank_account_number=bank_account_number,
            )

        existing_payment = Payment.objects.filter(
            user=user,
            vessel=self.vessel,
            start_date=start_date,
            end_date=end_date,
        ).first()

        if existing_payment:
            raise ValidationError(
                f"Payment already exists for user '{user} \
                            for the period {start_date.strftime('%b %d, %Y')} - \
                                {end_date.strftime('%b %d, %Y')}."
            )

        return cleaned_data

    def validate_cash_fields(
        self,
        cash_currency,
        cash_amount,
        cash_exchange_rate,
        cash_beneficiary_name,
        cash_beneficiary_relationship,
        cash_beneficiary_contact,
    ):
        if not cash_currency:
            self.add_error("cash_currency", "Cash currency is required.")

        if cash_currency and cash_currency == "USD":
            if not cash_amount:
                self.add_error(
                    "cash_amount",
                    "Cash amount is required because you select USD currency.",
                )
        elif cash_currency and cash_currency != "USD":
            if not cash_exchange_rate:
                self.add_error("cash_exchange_rate", "Cash exchange rate is required.")

        if cash_beneficiary_relationship != "crew_member":
            if not cash_beneficiary_name:
                self.add_error(
                    "cash_beneficiary_name",
                    "Cash beneficiary name is required.",
                )
            if not cash_beneficiary_contact:
                self.add_error(
                    "cash_beneficiary_contact", "Cash beneficiary contact is required."
                )

    def validate_bank_transfer_fields(
        self,
        bank_transfer_currency,
        bank_transfer_amount,
        bank_transfer_exchange_rate,
        bank_transfer_beneficiary_name,
        bank_transfer_beneficiary_relationship,
        bank_transfer_beneficiary_contact,
        bank_name,
        bank_account_name,
        bank_account_number,
    ):
        if not bank_transfer_currency:
            self.add_error(
                "bank_transfer_currency", "Bank transfer currency is required."
            )

        if bank_transfer_currency and bank_transfer_currency == "USD":
            if not bank_transfer_amount:
                self.add_error(
                    "bank_transfer_amount",
                    "Bank transfer USD amount is required\
                               because you selected USD currency.",
                )
        elif bank_transfer_currency and bank_transfer_currency != "USD":
            if not bank_transfer_exchange_rate:
                self.add_error(
                    "bank_transfer_exchange_rate",
                    "Bank transfer exchange rate is required.",
                )

        if bank_transfer_beneficiary_relationship != "crew_member":
            if not bank_transfer_beneficiary_name:
                self.add_error(
                    "bank_transfer_beneficiary_name",
                    "Bank transfer beneficiary\
                               name is required.",
                )
            if not bank_transfer_beneficiary_contact:
                self.add_error(
                    "bank_transfer_beneficiary_contact",
                    "Bank transfer beneficiary contact is required.",
                )

        if not bank_account_name:
            self.add_error("bank_account_name", "Bank account name is required.")
        if not bank_account_number:
            self.add_error("bank_account_number", "Bank account number is required.")
        if not bank_name:
            self.add_error("bank_name", "Bank name is required.")


class BasePaymentFormSet(BaseModelFormSet):
    def __init__(self, *args, vessel=None, loggedin_user=None, **kwargs):
        self.vessel = vessel
        self.loggedin_user = loggedin_user
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs["vessel"] = self.vessel
        kwargs["loggedin_user"] = self.loggedin_user
        return super()._construct_form(i, **kwargs)

    def clean(self):
        non_empty_forms = []
        for form in self.forms:
            # Check raw data to determine if the form is empty
            if any(
                form.cleaned_data.get(field)
                for field in form.cleaned_data
                if field != "DELETE"
            ):
                non_empty_forms.append(form)
            else:
                # Reset errors for completely empty forms
                form.cleaned_data = {}
                form._errors = {}

        if not non_empty_forms:
            self._non_form_errors = self.error_class(["Please add a payment."])
        else:
            self.forms = non_empty_forms

        return super().clean()


PaymentsFormSet = modelformset_factory(
    Payment, form=AddPaymentsForm, formset=BasePaymentFormSet, extra=3
)
