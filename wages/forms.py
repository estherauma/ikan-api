from django import forms
from vessels.models import Vessel
from wages.models import Wage
from django.forms import modelformset_factory, BaseModelFormSet
from django.core.exceptions import ValidationError
from wages.utils import (
    wage_fields,
    get_workers_on_vessel,
    generate_beneficiary_relationship_options,
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
    payslip = forms.FileField(required=False)
    crew_bank_transfer_receipt = forms.FileField(required=False)
    beneficiary_bank_transfer_receipt = forms.FileField(required=False)
    beneficiary_relationship = forms.ChoiceField()

    class Meta:
        model = Wage
        # We are listing the fields instead of using exclude
        # to control their order in the row when displaying
        fields = wage_fields

    def __init__(self, *args, vessel=None, loggedin_user=None, payments_common_text={}, **kwargs):
        super().__init__(*args, **kwargs)
        self.vessel = vessel
        self.payments_common_text = payments_common_text
        file_fields = ["payslip", "crew_bank_transfer_receipt", "beneficiary_bank_transfer_receipt"]
        empty_select_choice = [("", "")]

        for field in self.fields:
            self.fields[field].widget.attrs["style"] = "min-height: 45px; border-radius: 10px;\
                border-width: 1px; min-width: 100px; max-width: 160px;padding: 0 10px; font-size: 1rem;"
            if field in file_fields:
                self.fields[field].widget.attrs["accept"] = ".pdf,.jpg,.jpeg,.png"
            if field == "usd_amount":
                self.fields[field].widget.attrs["step"] = "0.01"
                self.fields[field].widget.attrs["min"] = "0"
                self.fields[field].widget.attrs["placeholder"] = "0.00"

        self.fields["user"].widget.attrs["style"] += "max-width: 250px;"
        for field in file_fields:
            self.fields[field].widget.attrs["style"] += "max-width: 250px;"

        beneficiary_relationship_options = generate_beneficiary_relationship_options(payments_common_text)
        self.fields["beneficiary_relationship"].choices = empty_select_choice + [(item["key"], item["label"]) for item
                                                                                 in beneficiary_relationship_options]

        if vessel:
            workers_on_vessel = get_workers_on_vessel(vessel)
            self.fields["user"].queryset = workers_on_vessel

    def clean_usd_amount(self):
        usd_amount = self.cleaned_data.get("usd_amount")
        if usd_amount is not None and usd_amount <= 0:
            raise self.add_error("usd_amount", "Amount cannot be 0 or negative..")
        return usd_amount

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get("user")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        beneficiary_name = cleaned_data.get("beneficiary_name")
        beneficiary_relationship = cleaned_data.get("beneficiary_relationship")
        beneficiary_contact = cleaned_data.get("beneficiary_contact")

        if start_date and end_date and end_date <= start_date:
            self.add_error("end_date", "End date must be after start date.")

        # TODO: Check if payments can be made before/after end and start dates
        # if payment_date and start_date and payment_date < start_date:
        #     self.add_error("payment_date", "Payment date cannot be before the start date.")

        # if payment_date and end_date and payment_date > end_date:
        #     self.add_error("payment_date", "Payment date cannot be after the end date.")

        if not beneficiary_relationship:
            self.add_error("beneficiary_relationship", "Beneficiary relationship is required.")
        if beneficiary_relationship and beneficiary_relationship != "self":
            if not beneficiary_name:
                self.add_error("beneficiary_name", "Beneficiary name is required.")
            if not beneficiary_contact:
                self.add_error("beneficiary_contact", "Beneficiary contact is required.")

        existing_wage = Wage.objects.filter(
            user=user,
            vessel=self.vessel,
            start_date=start_date,
            end_date=end_date,
        ).first()
        if existing_wage:
            raise ValidationError(
                f"Payment already exists for user '{user} \
                            for the period {start_date.strftime('%b %d, %Y')} - \
                                {end_date.strftime('%b %d, %Y')}."
            )

        return cleaned_data


class BaseWageFormSet(BaseModelFormSet):
    def __init__(self, *args, vessel=None, loggedin_user=None, payments_common_text={}, **kwargs):
        self.vessel = vessel
        self.payments_common_text = payments_common_text
        self.loggedin_user = loggedin_user
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs["vessel"] = self.vessel
        kwargs["loggedin_user"] = self.loggedin_user
        kwargs["payments_common_text"] = self.payments_common_text
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

    # Overrides the default empty_form method to set the custom queryset for the user field
    def empty_form(self):
        form = self.form(
            auto_id=self.auto_id,
            prefix=self.add_prefix("__prefix__"),
            empty_permitted=True,
            use_required_attribute=False,
            **self.get_form_kwargs(None),
            renderer=self.renderer,
        )
        self.add_fields(form, None)

        # set the queryset for the user field in the empty form to the workers on the vessel
        workers_on_vessel = get_workers_on_vessel(self.vessel)
        form.fields["user"].queryset = workers_on_vessel

        return form


WagesFormSet = modelformset_factory(
    Wage,
    form=AddWageForm,
    formset=BaseWageFormSet,
    extra=3,
)
