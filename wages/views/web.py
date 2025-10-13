from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from wages.models import Wage
from django.contrib import messages
from payments.utils import (
    methods_map,
    payment_fields,
    cash_fields,
    bank_transfer_fields,
    deduction_fields,
    # get_workers_on_vessel,
    get_formset_initial_values,
    generate_payment_field_labels,
    generate_payment_currency_options,
    generate_deductions_options,
)
from wages.utils import (
    wage_fields,
    get_workers_on_vessel,
    generate_wage_field_labels,
)
from vessels.models import Vessel
from django.views.generic import DetailView
from wages.forms import VesselSelectForm, WagesFormSet
from payments.forms import PaymentsFormSet
from notifications.models import Notification
import json
from prismic.utils import PrismicUtils


class WageListView(LoginRequiredMixin, ListView):
    model = Wage
    context_object_name = "wages"
    template_name = "wages_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        is_super_user = user.is_superuser
        roles = user.groups.all().values_list("name", flat=True)
        has_vessel = Vessel.objects.filter(created_by=user.id).exists()
        wages = Wage.objects.filter(created_by=user.id)
        if is_super_user:
            wages = Wage.objects.all()
        elif "worker" in roles:
            wages = Wage.objects.filter(user=user)

        context["wages"] = wages
        context["has_vessel"] = has_vessel
        context["vessel_form"] = VesselSelectForm(user=user)

        # group wages by vessel
        if wages:
            grouped_wages = {}
            for wage in wages:
                if wage.vessel.name not in grouped_wages:
                    grouped_wages[wage.vessel.name] = []
                grouped_wages[wage.vessel.name].append(wage)
            grouped_wages = dict(sorted(grouped_wages.items()))
            context["grouped_wages"] = grouped_wages

        # Get payments common text
        prismic_utils = PrismicUtils(self.request)
        context["payments_common_text"] = prismic_utils.get_page_text("payments-common-text")

        return context


class WageDetailView(LoginRequiredMixin, DetailView):
    model = Wage
    context_object_name = "wage"
    template_name = "wage_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wage = self.get_object()
        context["wage"] = wage

        # Get payments common text
        prismic_utils = PrismicUtils(self.request)
        context["payments_common_text"] = prismic_utils.get_page_text("payments-common-text")

        return context


class SelectVesselView(LoginRequiredMixin, View):
    def get(self, request):
        form = VesselSelectForm(user=request.user)
        return render(request, "wages_list.html", {"vessel_form": form})

    def post(self, request):
        form = VesselSelectForm(data=request.POST, user=request.user)
        if form.is_valid():
            selected_vessel = form.cleaned_data["vessel"]
            vessel_id = selected_vessel.id
            request.session["vessel_id"] = vessel_id
            return redirect("wages:add-wages")

        else:
            messages.error(request, "Form is invalid.")
            return redirect("wages:wages-list")


class AddWagesView(LoginRequiredMixin, View):
    template_name = "add_wages.html"

    def get_context_data(self, **kwargs):
        context = {}

        prismic_utils = PrismicUtils(self.request)
        payments_common_text = prismic_utils.get_page_text("payments-common-text")
        vessel_id = self.request.session.get("vessel_id")
        vessel = get_object_or_404(Vessel, pk=vessel_id)
        workers_on_vessel = get_workers_on_vessel(vessel)
        formset = WagesFormSet(
            queryset=Wage.objects.none(),
            vessel=vessel,
            loggedin_user=self.request.user,
            payments_common_text=payments_common_text
        )

        context = {
            **context,
            "vessel": vessel,
            "formset": formset,
            "wage_fields": wage_fields,
            "workers_on_vessel": workers_on_vessel,
            "payments_common_text": payments_common_text,
            "json_payments_common_text": json.dumps(
                payments_common_text,
            ),
            "field_labels": generate_wage_field_labels(
                payments_common_text,
            ),
        }

        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)