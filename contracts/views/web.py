from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views import generic
from django.views.generic import CreateView
from accounts.models import User
from contracts.forms import ContractAccessForm, AddContractForm
from contracts.models import Contract, UserContractAccess, ContractDocument
import json
from common.utils import get_clause_order
from django.contrib import messages
from django.db.models import Q
from common.utils import generate_uuid
import os


class ContractsView(LoginRequiredMixin, View):
    def get_context_data(self, **kwargs):
        context = kwargs
        user = self.request.user
        if user.is_superuser:
            contracts = Contract.objects.all()
        else:
            contracts = Contract.objects.filter(
                Q(created_by=user.id) |
                Q(contract_user_access__user=user.id)
            ).distinct()
        context['contracts'] = contracts
        context['new_contract_form'] = AddContractForm(user=user)

        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, 'contracts/list.html', context)


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


class AddContractView(LoginRequiredMixin, View):
    def get_context_data(self, **kwargs):
        context = kwargs
        user = self.request.user
        if user.is_superuser:
            contracts = Contract.objects.all()
        else:
            contracts = Contract.objects.filter(
                Q(created_by=user.id) |
                Q(contract_user_access__user=user.id)
            ).distinct()
        context['contracts'] = contracts
        context['new_contract_form'] = AddContractForm(user=user)
        return context

    def get(self, request):
        context = self.get_context_data()
        return render(request, 'contracts/list.html', context)

    def post(self, request):
        form = AddContractForm(data=request.POST, files=request.FILES, user=request.user)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.taiwanese_company = form.cleaned_data['taiwanese_company'] if form.cleaned_data['taiwanese_company'] else None
            contract.indonesian_company = form.cleaned_data['indonesian_company'] if form.cleaned_data['indonesian_company'] else None
            contract.created_by = request.user.id
            contract.updated_by = request.user.id
            contract.app_ref = generate_uuid()
            contract.save()

            if 'contract_signature' in request.FILES:
                if not os.path.exists('uploads/contracts'):
                    os.makedirs('uploads/contracts')

                file_name = request.FILES['contract_signature'].name
                file_path = f'uploads/contracts/{request.user.id}_ikan_{file_name}'
                with open(file_path, 'wb+') as destination:
                    for chunk in request.FILES['contract_signature'].chunks():
                        destination.write(chunk)

                contract_document = ContractDocument.objects.create(
                    contract=contract,
                    url=file_path,
                    name=file_name,
                    created_by=request.user.id,
                    updated_by=request.user.id,
                )
                contract_document.save()
            messages.success(request, 'Contract created successfully')
            return render(request, 'contracts/list.html', self.get_context_data())
        else:
            messages.error(request, 'Error creating contract')
            return render(request, 'contracts/list.html', self.get_context_data())
