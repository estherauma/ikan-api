from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views import generic
from django.views.generic import CreateView
from accounts.models import User
from contracts.forms import ContractAccessForm, AddContractForm
from contracts.models import Contract, UserContractAccess, ContractDocument, ContractClause
import json
from django.contrib import messages
from django.db.models import Q
from common.utils import generate_uuid
import os
from contracts.utils import (
    generate_static_contract_clauses,
    get_clause_order,
    get_clauses_to_be_added,
    get_clause_form_questions,
    get_clause_html_content,
)
from prismic.utils import PrismicUtils
import datetime


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

                # generate static clauses
                generate_static_contract_clauses(request, contract)
            messages.success(request, 'Contract created successfully')
            return redirect('contracts-web:contract-details', pk=contract.id)
        else:
            messages.error(request, 'Error creating contract')
            return render(request, 'contracts/list.html', self.get_context_data())


class ContractsDetailView(LoginRequiredMixin, generic.DetailView):
    model = Contract
    template_name = 'contracts/view.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context['clauses'] = self.object.contract_clause.all()

        for item in context['clauses']:
            item.order = item.order if item.order else get_clause_order(item.kind)
            item.content = json.loads(item.content)
            item.html_content = get_clause_html_content(request=self.request, clause=item)

        clauses = sorted(context['clauses'], key=lambda x: x.order)
        clauses_to_be_added = get_clauses_to_be_added(self.request, self.object)

        context['clauses'] = clauses
        context['clauses_to_be_added'] = clauses_to_be_added
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

    def post(self, request, *args, **kwargs):
        prismic_utils = PrismicUtils(request)
        contract = self.get_object()

        clause_kind = request.POST.get('clause_kind')
        page_title = request.POST.get('page_title')
        form_questions = get_clause_form_questions(request, clause_kind)
        Form = prismic_utils.create_form(form_questions)
        form = Form(request.POST, request.FILES)
        if form.is_valid():
            clause_data = {
                key: value.isoformat() if isinstance(value, datetime.date) else value
                for key, value in form.cleaned_data.items()
            }

            clause = ContractClause.objects.create(
                app_ref=generate_uuid(),
                contract=contract,
                name=page_title,
                kind=clause_kind,
                content=json.dumps(clause_data),
                created_by=request.user.id,
                updated_by=request.user.id,
            )
            clause.save()

            messages.success(request, 'Clause added successfully')
            return redirect('contracts-web:contract-details', pk=contract.id)
        else:
            # TODO: continue displaying form if invalid
            messages.error(request, 'Error adding clause')
            context = self.get_context_data()
            return render(request, self.template_name, context)


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
