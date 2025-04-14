from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from payments.models import Payment
from django.contrib import messages
from payments.utils import (
    methods_map,
    categories_map,
    payment_fields,
    payment_fields_map_english,
    payment_fields_map_chinese,
    cash_fields,
    bank_transfer_fields,
    deduction_fields,
    get_workers_on_vessel,
)
from vessels.models import Vessel
from django.views.generic import DetailView
from payments.forms import VesselSelectForm, PaymentsFormSet
from notifications.models import Notification
import json


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    context_object_name = "payments"
    template_name = "payments_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        is_super_user = user.is_superuser
        roles = user.groups.all().values_list("name", flat=True)
        has_vessel = Vessel.objects.filter(created_by=user.id).exists()
        payments = Payment.objects.filter(created_by=user.id)
        if is_super_user:
            payments = Payment.objects.all()
        elif "worker" in roles:
            payments = Payment.objects.filter(user=user)

        context["payments"] = payments
        context["has_vessel"] = has_vessel
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["methods_map"] = methods_map
        context["categories_map"] = categories_map
        return context


class SelectVessel(LoginRequiredMixin, View):
    def get(self, request):
        form = VesselSelectForm(user=request.user)
        return render(request, "payments_list.html", {"vessel_form": form})

    def post(self, request):
        form = VesselSelectForm(data=request.POST, user=request.user)
        if form.is_valid():
            selected_vessel = form.cleaned_data["vessel"]
            vessel_id = selected_vessel.id
            request.session["vessel_id"] = vessel_id
            return redirect("payments:add-payments")

        else:
            messages.error(request, "Form is invalid.")
            return redirect("payments:payments-list")


class AddPayment(LoginRequiredMixin, View):
    template_name = "add_payments.html"

    def get(self, request):
        vessel_id = self.request.session.get("vessel_id")
        vessel = get_object_or_404(Vessel, pk=vessel_id)
        workers_on_vessel = get_workers_on_vessel(vessel)
        formset = PaymentsFormSet(
            queryset=Payment.objects.none(), vessel=vessel, loggedin_user=request.user
        )
        return render(
            request,
            self.template_name,
            {
                "vessel": vessel,
                "formset": formset,
                "payment_fields": payment_fields,
                "english_fields": payment_fields_map_english,
                "chinese_fields": payment_fields_map_chinese,
                "cash_fields": cash_fields,
                "bank_transfer_fields": bank_transfer_fields,
                "workers_on_vessel": workers_on_vessel,
                "deduction_fields": deduction_fields,
            },
        )

    def post(self, request):
        vessel_id = self.request.session.get("vessel_id")
        vessel = get_object_or_404(Vessel, pk=vessel_id)
        workers_on_vessel = get_workers_on_vessel(vessel)
        formset = PaymentsFormSet(
            request.POST, vessel=vessel, loggedin_user=request.user
        )

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.vessel = vessel
                instance.created_by = request.user.id
                instance.updated_by = request.user.id

                instance.save()

                # Create payment notification
                try:
                    self.send_payment_notification(instance, vessel)
                except Exception as e:
                    print(f"Failed to send notification: {e}")

            # Save many-to-many data if applicable
            formset.save_m2m()
            return redirect("payments:payments-list")
        else:
            return render(
                request,
                self.template_name,
                {
                    "vessel": vessel,
                    "formset": formset,
                    "payment_fields": payment_fields,
                    "english_fields": payment_fields_map_english,
                    "chinese_fields": payment_fields_map_chinese,
                    "cash_fields": cash_fields,
                    "bank_transfer_fields": bank_transfer_fields,
                    "workers_on_vessel": workers_on_vessel,
                    "deduction_fields": deduction_fields,
                },
            )

    def send_payment_notification(self, payment, vessel):
        notif_data = {
            'payment_id': payment.id,
            'vessel_id': vessel.id,
            'vessel_name': vessel.name,
            'amount': float(payment.total_usd_amount_received),
            'currency': 'USD',
            'payment_date': payment.payment_date.isoformat(),
        }
        json_notif_data = json.dumps(notif_data)

        Notification.objects.create(
            user=payment.user,
            category='payment',
            title='Payment Received',
            message=f'Payment of {payment.total_usd_amount_received:.2f} USD received for {vessel.name}.',
            status='unread',
            is_displayed=False,
            is_deleted=False,
            metadata=json_notif_data,
            created_by=payment.created_by,
            updated_by=payment.updated_by,
        )
