from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views import generic
from django.views.generic import CreateView
from accounts.models import User
from contracts.forms import ContractAccessForm
from contracts.models import Contract, UserContractAccess
import json
from common.utils import get_clause_order
from django.contrib import messages


class ContractsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'contracts/list.html')


class ContractsDetailView(LoginRequiredMixin, generic.DetailView):
    model = Contract
    template_name = 'contracts/view.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['clauses'] = self.object.contract_clause.all()

        for item in context['clauses']:
            item.order = item.order if item.order else get_clause_order(item.kind)
            item.content = json.loads(item.content)

        context['clauses'] = sorted(context['clauses'], key=lambda x: x.order)
        context['access_users'] = self.get_access_users()
        return context

    def get_access_users(self):
        access_users = UserContractAccess.objects.filter(
            contract=self.object
        ).select_related('user')

        # Create a set of users from the access_users queryset
        users_set = set(access.user for access in access_users)

        # Add the contract's creator to the set of users
        users_set.add(User.objects.get(pk=self.object.created_by))

        return users_set


class ContractsDataView(LoginRequiredMixin, View):
    def get(self, request):
        super_user = self.request.user.is_superuser
        contracts = Contract.objects.all() if super_user else Contract.objects.filter(created_by=request.user.id)
        contracts_list = []
        for contract in contracts:
            contract = {
                "id": contract.id,
                "name": contract.name,
                "app_ref": contract.app_ref,
                "internal_ref": contract.internal_ref,
                "start_date": contract.start_date,
                "end_date": contract.end_date,
                "description": contract.description,
                "taiwanese_company": contract.taiwanese_company,
                "indonesian_company": contract.indonesian_company,
                "kind": contract.kind,
                "actions": "<a href='/contracts/" + str(contract.id) +
                           "' class='btn btn-primary btn-sm'><i class='mdi mdi-eye'></i> View</a>"
            }
            contracts_list.append(contract)
        return JsonResponse({'data': contracts_list})


class ContractAccessView(CreateView):
    model = UserContractAccess
    form_class = ContractAccessForm
    template_name = 'contracts/add_access.html'

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(
                request=self.request,
                **self.get_form_kwargs()
            )

    def get_initial(self):
        initial = super().get_initial()
        initial['contract'] = self.kwargs.get('pk')
        return initial

    def get_success_url(self):
        return reverse_lazy(
            'contracts-web:contract-details',
            kwargs={'pk': self.object.contract.pk}
        )

    def form_valid(self, form):
        if UserContractAccess.objects.filter(
            user=form.cleaned_data['user'],
            contract=form.cleaned_data['contract']
        ).exists():
            messages.error(self.request, 'Access already granted')
            return self.form_invalid(form)
        messages.success(self.request, 'Access granted successfully')
        return super(ContractAccessView, self).form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)
