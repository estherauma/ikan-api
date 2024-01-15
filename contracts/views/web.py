from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views import generic


# mode imports
from contracts.models import Contract

import json 

class ContractsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'contracts/list.html')
    
class ContractsDetailView(LoginRequiredMixin, generic.DetailView):
    model = Contract
    template_name = 'contracts/view.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['clauses'] = self.object.contract_clause.all()
        return context


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
                "actions": "<a href='/contracts/" + str(contract.id) + "' class='btn btn-primary btn-sm'><i class='mdi mdi-eye'></i> View</a>"
            }
            contracts_list.append(contract)
        return JsonResponse({'data': contracts_list})   