from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View


# mode imports
from contracts.models import Contract

import json 

class ContractsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'contracts.html')
    
class ContractsDataView(LoginRequiredMixin, View):
    def get(self, request):
        contracts = Contract.objects.all()
        contracts_list = []
        for contract in contracts:
            contract_dict = {
                'id': contract.id,
                'name': contract.name,
                'app_ref': contract.app_ref,
                'internal_ref': contract.internal_ref,
                'start_date': contract.start_date,
                'end_date': contract.end_date,
                'description': contract.description,
                'taiwanese_company': contract.taiwanese_company,
                'indonesian_company': contract.indonesian_company,
                'kind': contract.kind,
                'something': '<a href="/contracts/edit/' + str(contract.id) + '" class="btn btn-primary btn-sm">Edit</a>' 
            }
            contracts_list.append(contract_dict)
        return JsonResponse({'data': contracts_list})   