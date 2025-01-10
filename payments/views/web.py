from django.http import HttpResponse
from django.views import View
from django.shortcuts import render, redirect
from payments.forms import UploadPaymentsForm
import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from payments.models import Payment
from django.contrib import messages
import pandas as pd
from payments.utils import (
    display_col_name_to_key_map,
    methods_map,
    boolean_values_map,
    initial_required_fields,
    required_cash_fields,
    required_bank_transfer_fields,
    currencies_map,
)
from vessels.models import Vessel
from accounts.models import User
from django.views.generic import DetailView
from payments.forms import VesselSelectForm


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    context_object_name = "payments"
    template_name = "payments_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        is_super_user = user.is_superuser
        roles = user.groups.all().values_list("name", flat=True)
        payments = Payment.objects.filter(created_by=user.id)
        if is_super_user:
            payments = Payment.objects.all()
        elif "worker" in roles:
            payments = Payment.objects.filter(user=user)

        context["payments"] = payments
        context["upload_payments_form"] = UploadPaymentsForm()
        context["vessel_form"] = VesselSelectForm(user=user)

        # group payments by vessel
        if payments:
            grouped_payments = {}
            for payment in payments:
                if payment.vessel.name not in grouped_payments:
                    grouped_payments[payment.vessel.name] = []
                grouped_payments[payment.vessel.name].append(payment)
            grouped_payments = dict(sorted(grouped_payments.items()))
            context["grouped_payments"] = grouped_payments

        return context


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = "payment_detail.html"


class PaymentUploadView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "payments_list.html")

    def post(self, request):
        form = UploadPaymentsForm(request.POST, request.FILES)
        if form.is_valid():
            payments_file = request.FILES["file"]

            accepted_file_types = ["xlsx", "xls"]
            if payments_file.name.split(".")[-1] not in accepted_file_types:
                messages.error(
                    request,
                    "File type not supported. Please upload a .xlsx or .xls file.",
                )
                return redirect("payments:payments-list")

            df = pd.read_excel(payments_file, engine="openpyxl", header=1)
            df.replace(0, pd.NA, inplace=True)
            df = df.where(pd.notnull(df), None)
            df = df.dropna(how="all")  # Remove blank rows

            mapped_columns = {}
            for col in df.columns:
                if col in display_col_name_to_key_map:
                    mapped_columns[col] = display_col_name_to_key_map[col]
                else:
                    messages.error(
                        request, f"Column '{col}' is not supported. Contact Admin."
                    )
                    print(
                        f"Warning: Column '{col}' does not have a mapping and will be skipped."
                    )

            df.rename(columns=mapped_columns, inplace=True)

            for row in df.iloc[1:].itertuples(index=False):
                # Create a dictionary of field-value pairs
                record = {key: getattr(row, key) for key in mapped_columns.values()}

                # format data to match model data types
                format_record(record)

                # Check if all required fields are present
                missing_fields = []
                required_fields = initial_required_fields
                if record["payment_method"] == "cash":
                    required_fields = initial_required_fields + required_cash_fields
                elif record["payment_method"] == "bank_transfer":
                    required_fields = (
                        initial_required_fields + required_bank_transfer_fields
                    )

                for field in required_fields:
                    value = record.get(field)
                    if not isinstance(value, bool) and not value:
                        missing_fields.append(field)

                if missing_fields:
                    messages.error(
                        request,
                        f"Missing fields: {', '.join(missing_fields)} for user {record.get('crew_name')}.",
                    )
                    continue

                # Check if the vessel and user exist
                vessel = Vessel.objects.filter(name=record["vessel_name"]).first()
                if vessel:
                    record["vessel"] = vessel
                else:
                    messages.error(
                        request, f"Vessel '{record['vessel_name']}' not found."
                    )
                    continue

                names = record["crew_name"].split()
                first_name = names[0] if names else ""
                last_name = names[1] if len(names) > 1 else ""
                user = User.objects.filter(
                    first_name=first_name,
                    last_name=last_name,
                ).first()
                if user:
                    record["user"] = user
                else:
                    messages.error(request, f"User '{record['crew_name']}' not found.")
                    continue

                # Check if the payment period is valid
                try:
                    start_date = pd.to_datetime(
                        record.get("start_date"), errors="raise"
                    )
                    end_date = pd.to_datetime(record.get("end_date"), errors="raise")
                except Exception as e:
                    messages.error(
                        request,
                        f"Invalid payment period start or end date for user '{record.get('crew_name')}'.",
                    )
                    print(
                        f"Error: Invalid payment period start or end date for user '{record.get('crew_name')}'. {e}"
                    )
                    continue

                # Check if the payment already exists
                existing_payment = Payment.objects.filter(
                    user=user,
                    vessel=vessel,
                    start_date=start_date,
                    end_date=end_date,
                ).first()

                if existing_payment:
                    messages.error(
                        request,
                        f"Payment already exists for user '{record.get('crew_name')} \
                            for the period {start_date.strftime('%b %d, %Y')} - \
                                {end_date.strftime('%b %d, %Y')}.",
                    )
                    continue  # Skip this record if it already exists

                # Save the record to the database
                try:
                    crew_name = record.get("crew_name")
                    # TODO: remove unnecessary fields and save deductions
                    del record["vessel_name"]
                    del record["crew_name"]
                    del record["deduction_1"]
                    del record["deduction_1_reason"]
                    del record["deduction_1_other_reason"]
                    del record["deduction_2"]
                    del record["deduction_2_reason"]
                    del record["deduction_2_other_reason"]

                    record["created_by"] = request.user.id
                    record["updated_by"] = request.user.id

                    payment = Payment(**record)
                    payment.save()
                    messages.success(
                        request,
                        f"Payment saved for user '{crew_name}' \
                            for the period {start_date.strftime('%b %d, %Y')} - \
                                {end_date.strftime('%b %d, %Y')}.",
                    )
                except Exception as e:
                    messages.error(
                        request,
                        f"Failed to save payment for user '{crew_name}' \
                            for the period {start_date.strftime('%b %d, %Y')} - \
                                {end_date.strftime('%b %d, %Y')}.",
                    )
                    print(f"Error: Failed to save payment for user '{crew_name}'. {e}")

        else:
            messages.error(request, "Form is invalid.")

        return redirect("payments:payments-list")


def format_record(record):
    for key, value in record.items():
        if value is not None and isinstance(value, str):
            record[key] = value.strip()

        if (
            key == "is_bank_transfer_beneficiary_crew"
            or key == "is_cash_beneficiary_crew"
            or key == "has_deductions"
        ):
            if value is None:
                record[key] = False
            else:
                record[key] = boolean_values_map[value.strip()]

        if key == "payment_method":
            if value:
                record[key] = methods_map[value.strip()]

        if key == "cash_currency" or key == "bank_transfer_currency":
            if value:
                record[key] = currencies_map[value.strip()]


# TODO: rework template download
def download_template_file(request):
    # Change to fields in the Payment model
    columns = ["Vessel Name", " Crew Name", "Amount", "Date", "Description"]
    # rules = {}

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="Payments_template.csv"'

    writer = csv.writer(response)
    writer.writerow(columns)
    return response


class SelectVessel(LoginRequiredMixin, View):
    def get(self, request):
        form = VesselSelectForm(user=request.user)
        return render(request, "payments_list.html", {'vessel_form': form})

    def post(self, request):
        form = VesselSelectForm(data=request.POST, user=request.user)
        if form.is_valid():
            selected_vessel = form.cleaned_data['vessel']
            vessel_id = selected_vessel.id
            return render(request, 'add_payments.html', {'vessel_id': vessel_id})

        else:
            messages.error(request, "Form is invalid.")
            return redirect("payments:payments-list")
