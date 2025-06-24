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
    get_clause_form,
    get_clause_html_content,
    dynamic_clauses,
)
from prismic.utils import PrismicUtils
import datetime
from companies.models import Company


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
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context['clauses'] = self.object.contract_clause.all()
        if self.object.taiwanese_company:
            taiwan_company = Company.objects.filter(
                id=self.object.taiwanese_company
            ).first()
            if taiwan_company:
                self.object.taiwanese_company_name = taiwan_company.name
        if self.object.indonesian_company:
            indonesian_company = Company.objects.filter(
                id=self.object.indonesian_company
            ).first()
            if indonesian_company:
                self.object.indonesian_company_name = indonesian_company.name

        for item in context['clauses']:
            # Get clause order. For ordering clauses properly when displaying
            item.order = item.order if item.order else get_clause_order(item.kind)

            item.content = json.loads(item.content)
            if item.kind == 'contract-clauses-parties-requirement-vessel':
                # TODO: translate
                item.name = 'Parties to this Contract'
                # Add party B id to party A details
                party_b_clause = context['clauses'].filter(kind='contract-clauses-parties-requirement-fishers').first()
                if party_b_clause:
                    item.has_party_b_clause = True
                    party_b_clause_id = party_b_clause.id
                    if isinstance(item.content, str):
                        try:
                            item.content = json.loads(item.content)
                        except json.JSONDecodeError:
                            item.content = {}
                    item.content = {**item.content, 'party_b_clause_id': party_b_clause_id}
                else:
                    item.has_party_b_clause = False

            # Get clause text (html content) to be displayed
            item.html_content = get_clause_html_content(request=self.request, clause=item)

            # Check if clause is dynamic
            item.is_dynamic = True if item.kind in dynamic_clauses else False

            # Get clause form (for editing)
            # Different from clauses_to_be_added, because these already exist in the contract
            if item.is_dynamic:
                item.content['clause_kind'] = item.kind
                item.form = get_clause_form(self.request, item.kind, item.content)

        clauses = sorted(context['clauses'], key=lambda x: x.order)

        # get party B index  # should be after sorting
        party_b_index = next((i for i, obj in enumerate(clauses) if obj.kind ==
                              'contract-clauses-parties-requirement-fishers'), None)
        if party_b_index is not None:
            context['party_b_index'] = party_b_index + 1  # +1 because template is using 1-based indexing

        # Clauses that do not exist yet in the contract
        clauses_to_be_added = get_clauses_to_be_added(self.request, self.object)

        context['clauses'] = clauses
        context['clauses_to_be_added'] = clauses_to_be_added
        context['access_users'] = self.get_access_users()

        # Get contract signature URL
        contract_signature = self.object.contract_document.first() if self.object.contract_document.exists() else None
        if contract_signature:
            self.object.contract_signature_url = contract_signature.url  # for the contract detail view
        initial_data = {
            'contract_signature': contract_signature.url if contract_signature else None,  # for the form
        }

        context['new_contract_form'] = AddContractForm(user=user, instance=self.object, initial=initial_data)
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

    def handle_clause_attachments_uploads(self, request):
        obj = {}
        if 'partyASignature' in request.FILES or 'partyBSignature' in request.FILES:
            if not os.path.exists('uploads/contract_clause_attachments'):
                os.makedirs('uploads/contract_clause_attachments')

            if 'partyASignature' in request.FILES:
                party_a_file_name = request.FILES['partyASignature'].name
                party_a_file_path = f'uploads/contract_clause_attachments/{request.user.id}_ikan_{party_a_file_name}'
                with open(party_a_file_path, 'wb+') as destination:
                    for chunk in request.FILES['partyASignature'].chunks():
                        destination.write(chunk)
                obj['partyASignature'] = party_a_file_path

            if 'partyBSignature' in request.FILES:
                party_b_file_name = request.FILES['partyBSignature'].name
                party_b_file_path = f'uploads/contract_clause_attachments/{request.user.id}_ikan_{party_b_file_name}'
                with open(party_b_file_path, 'wb+') as destination:
                    for chunk in request.FILES['partyBSignature'].chunks():
                        destination.write(chunk)
                obj['partyBSignature'] = party_b_file_path
        return obj

    def post(self, request, *args, **kwargs):
        """
        Handles update of contract details, update of clause details and addition of clauses.
        """
        contract = self.get_object()
        prismic_utils = PrismicUtils(request)

        if request.POST.get('contract_id'):  # CONTRACT UPDATE
            form = AddContractForm(request.POST, request.FILES, instance=contract, initial={}, user=request.user)
            if form.is_valid():
                contract = form.save(commit=False)
                contract.updated_by = request.user.id
                contract.save()

                if 'contract_signature' in request.FILES:
                    if not os.path.exists('uploads/contracts'):
                        os.makedirs('uploads/contracts')

                    file_name = request.FILES['contract_signature'].name
                    file_path = f'uploads/contracts/{request.user.id}_ikan_{file_name}'
                    with open(file_path, 'wb+') as destination:
                        for chunk in request.FILES['contract_signature'].chunks():
                            destination.write(chunk)

                    if contract.contract_document.exists():
                        # Update existing contract document
                        contract_document = contract.contract_document.first()
                        contract_document.url = file_path
                        contract_document.name = file_name
                        contract_document.updated_by = request.user.id
                        contract_document.save()
                    else:
                        # Create new contract document
                        contract_document = ContractDocument.objects.create(
                            contract=contract,
                            url=file_path,
                            name=file_name,
                            created_by=request.user.id,
                            updated_by=request.user.id,
                        )
                        contract_document.save()

                messages.success(request, 'Contract updated successfully')
                return redirect('contracts-web:contract-details', pk=contract.id)
            else:
                messages.error(request, 'Error updating contract')
                return redirect('contracts-web:contract-details', pk=contract.id)
        elif request.POST.get('edit_clause_id'):  # CLAUSE UPDATE
            clause_id = request.POST.get('edit_clause_id')
            if clause_id:
                clause = ContractClause.objects.get(pk=clause_id)
                form_questions = get_clause_form_questions(request, clause.kind)
                if clause.kind == 'contract-clauses-attachments' and clause.content:
                    # If clause is attachments, we need to add the existing signatures to the form
                    data = json.loads(clause.content)
                    if 'partyASignature' in data or 'partyBSignature' in data:
                        for qtn in form_questions:
                            if qtn['key'] == 'partyASignature' and 'partyASignature' in data:
                                qtn['is_required'] = False
                            elif qtn['key'] == 'partyBSignature' and 'partyBSignature' in data:
                                qtn['is_required'] = False
                Form = prismic_utils.create_form(form_questions)
                form = Form(request.POST, request.FILES)
                if form.is_valid():
                    form.cleaned_data = {k: v for k, v in form.cleaned_data.items() if v is not None}
                    initial_values = json.loads(clause.content) if clause.content else {}
                    new_data = {
                        key: value.isoformat() if isinstance(value, datetime.date) else value
                        for key, value in form.cleaned_data.items()
                    }
                    clause_data = {**initial_values, **new_data}

                    uploaded_files = self.handle_clause_attachments_uploads(request)
                    if uploaded_files:
                        clause_data.update(uploaded_files)

                    clause.content = json.dumps(clause_data)
                    clause.updated_by = request.user.id
                    clause.save()
                    messages.success(request, 'Clause updated successfully')
                    return redirect('contracts-web:contract-details', pk=contract.id)
                else:
                    messages.error(request, 'Error updating clause')
                    return render(request, self.template_name, self.get_context_data())
        else:  # CLAUSE ADDITION
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

                uploaded_files = self.handle_clause_attachments_uploads(request)
                if uploaded_files:
                    clause_data.update(uploaded_files)

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
