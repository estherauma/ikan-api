from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from wages.models import Wage
from django.contrib import messages
from wages.utils import (
    wage_fields,
    file_fields,
    get_workers_on_vessel,
    generate_wage_field_labels,
    get_status_label,
)
from vessels.models import Vessel
from django.views.generic import DetailView
from wages.forms import VesselSelectForm, WagesFormSet
from notifications.models import Notification
import json
from content.utils import ContentUtils
import os
import re
from common.utils import upload_file_to_gcs
from django.db.models import Q


class WageListView(LoginRequiredMixin, ListView):
    model = Wage
    context_object_name = "wages"
    template_name = "wages_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        is_super_user = user.is_superuser
        roles = user.groups.all().values_list("name", flat=True)
        is_vessel_owner = "vessel_owner" in roles
        is_agent = "taiwanese_agent" in roles or "indonesian_agent" in roles
        has_vessel = Vessel.objects.filter(created_by=user.id).exists()
        agent_vos = user.vessel_owners
        agent_has_vo = None
        if user.groups.filter(name__in={"taiwanese_agent", "indonesian_agent"}).exists():
            agent_has_vo = agent_vos is not None
            if agent_has_vo:
                agent_vo_ids = agent_vos.values_list("id", flat=True)
                has_vessel = Vessel.objects.filter(created_by_id__in=agent_vo_ids).exists()

        if is_super_user:
            wages = Wage.objects.all()
        else:
            wages = Wage.objects.filter(
                Q(user=user) |
                Q(created_by=user.id) |
                Q(user__recruited_by=user)
            ).distinct()

        # Get payments common text
        content_utils = ContentUtils(self.request)
        payments_common_text = content_utils.get_page_text("payments-common-text")
        context["payments_common_text"] = payments_common_text

        # add status label and class to each wage
        for wage in wages:
            status_object = get_status_label(wage.status, payments_common_text, is_vessel_owner)
            wage.status_class = status_object['class']
            wage.status_label = status_object['label']

        context["wages"] = wages
        context["is_agent"] = is_agent
        context["agent_has_vo"] = agent_has_vo
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

        return context


class WageDetailView(LoginRequiredMixin, DetailView):
    model = Wage
    context_object_name = "wage"
    template_name = "wage_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get payments common text
        content_utils = ContentUtils(self.request)
        payments_common_text = content_utils.get_page_text("payments-common-text")
        context["payments_common_text"] = payments_common_text

        user = self.request.user
        roles = user.groups.all().values_list("name", flat=True)
        is_vessel_owner = "vessel_owner" in roles
        wage = self.get_object()
        status_object = get_status_label(wage.status, payments_common_text, is_vessel_owner)
        wage.status_class = status_object['class']
        wage.status_label = status_object['label']
        context["wage"] = wage

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
            content_utils = ContentUtils(self.request)
            common_text = content_utils.common_text
            messages.error(request, common_text.get("formIsInvalid", "Form is invalid."))
            return redirect("wages:wages-list")


class AddWagesView(LoginRequiredMixin, View):
    template_name = "add_wages.html"

    def get_context_data(self, **kwargs):
        context = {}

        content_utils = ContentUtils(self.request)
        payments_common_text = content_utils.get_page_text("payments-common-text")
        vessel_id = self.request.session.get("vessel_id")
        vessel = get_object_or_404(Vessel, pk=vessel_id)
        agent_obj = self.request.user if self.request.user.groups\
            .filter(name__in={"taiwanese_agent", "indonesian_agent"}).exists() else None
        workers_on_vessel = get_workers_on_vessel(vessel, agent_obj=agent_obj)
        formset = WagesFormSet(
            queryset=Wage.objects.none(),
            vessel=vessel,
            loggedin_user=self.request.user,
            payments_common_text=payments_common_text,
            agent_obj=agent_obj
        )

        context = {
            **context,
            "vessel": vessel,
            "formset": formset,
            "wage_fields": wage_fields,
            "file_fields": file_fields,
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

    def post(self, request):
        context = self.get_context_data()
        vessel = context["vessel"]
        payments_common_text = context["payments_common_text"]
        formset = WagesFormSet(
            data=request.POST,
            files=request.FILES,
            vessel=vessel,
            loggedin_user=request.user,
            payments_common_text=payments_common_text,
            agent_obj=self.request.user if self.request.user.groups
            .filter(name__in={"taiwanese_agent", "indonesian_agent"}).exists() else None
        )
        context["formset"] = formset

        if formset.is_valid():
            # Ensure upload directory exists
            if not os.path.exists('uploads/wages'):
                os.makedirs('uploads/wages')

            instances = formset.save(commit=False)
            for form, instance in zip(formset.forms, instances):
                # Upload files to server
                for field_name in file_fields:
                    file = form.cleaned_data.get(field_name)
                    if file:
                        file_name = file.name
                        file_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file_name)  # Sanitize filename
                        file_path = f'wages/{instance.user.id}_ikan_{file_name}'
                        # save to gcs
                        upload_file_to_gcs(file, file_path)
                        setattr(instance, field_name, file_path)
                    else:
                        setattr(instance, field_name, None)

                instance.vessel = vessel
                instance.created_by = request.user
                instance.updated_by = request.user

                instance.save()

                # Create wage notification
                try:
                    self.send_wage_notification(instance, vessel)
                except Exception as e:
                    print(f"Error sending wage notification: {e}")

            # Save many-to-many data if applicable
            formset.save_m2m()

            messages.success(request, payments_common_text.get("wagePaymentsAddedSuccessfully",
                                                               "Wage payment(s) added successfully."))
            return redirect("wages:wages-list")
        else:
            messages.error(request, payments_common_text.get(
                "errorsInTheFormCorrectThemAndTryAgain",
                "There were errors in the form. Please correct them and try again."))
            context["formset"] = formset
            return render(request, self.template_name, context)

    def send_wage_notification(self, wage, vessel):
        notif_data = {
            'wage_id': wage.id,
            'vessel_id': vessel.id,
            'vessel_name': vessel.name,
            'crew_name': f'{wage.user.first_name} {wage.user.last_name}',
            'payment_date': str(wage.payment_date),
            'amount': float(wage.usd_amount),
        }
        json_notif_data = json.dumps(notif_data)
        Notification.objects.create(
            user=wage.user,
            category='wage-payment',
            title='New Wage Payment',
            message=f'Wage payment of {wage.usd_amount:.2f} USD received for {vessel.name}.',
            status='unread',
            metadata=json_notif_data,
            created_by=wage.created_by,
            updated_by=wage.updated_by,
        )
