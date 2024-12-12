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
from payments.utils import display_col_name_to_key_map


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    context_object_name = "payments"
    template_name = "payments_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upload_payments_form"] = UploadPaymentsForm()
        return context


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
            df = df.dropna(how="all")  # Remove blank rows

            mapped_columns = {}
            for col in df.columns:
                if col in display_col_name_to_key_map:
                    mapped_columns[col] = display_col_name_to_key_map[col]
                else:
                    messages.error(request, f"Column '{col}' is not supported.")
                    # TODO: change err msg
                    print(
                        f"Warning: Column '{col}' does not have a mapping and will be skipped."
                    )
                    # return redirect("payments:payments-list")

            df.rename(columns=mapped_columns, inplace=True)

            for row in df.iloc[1:].itertuples(index=False):
                # Create a dictionary of field-value pairs
                record_data = {
                    key: getattr(row, key) for key in mapped_columns.values()
                }
                print("record_data....", record_data)
                print("---------------------------------------------....---")

            messages.success(request, "Payments uploaded successfully.")
            return redirect("payments:payments-list")
        else:
            messages.error(request, "Form is invalid.")
            # print("Form is invalid------", form.errors)

        return redirect("payments:payments-list")


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
