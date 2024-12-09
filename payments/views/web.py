from django.http import HttpResponse
from django.views import View
from django.shortcuts import render, redirect
from payments.forms import UploadPaymentsForm
import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from payments.models import Payment
from django.contrib import messages


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

            if not payments_file.name.endswith(".csv"):
                messages.error(
                    request, "File type not supported. Please upload a CSV file."
                )
                return redirect("payments:payments-list")

            decoded_file = payments_file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            data = list(reader)

            for row in data:
                # add save logic
                print("rrrr", row)

            messages.success(request, "Payments uploaded successfully.")
            return redirect("payments:payments-list")
        else:
            messages.error(request, "Form is invalid.")
            # print("Form is invalid------", form.errors)

        return redirect("payments:payments-list")


def download_template_file(request):
    # Change to fields in the Payment model
    columns = ["Vessel Name", " Crew Name", "Amount", "Date", "Description"]
    # rules = {}

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="Payments_template.csv"'

    writer = csv.writer(response)
    writer.writerow(columns)
    return response
