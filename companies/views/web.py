from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import BaseModelForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from companies.models import Company
from django.views import generic

from contracts.forms import ContractAccessForm
from contracts.models import Contract, UserContractAccess

from django.views.generic.edit import FormView
from django.views.generic import CreateView

class CompaniesView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'companies/list.html')


class CompaniesDetailView(LoginRequiredMixin, generic.DetailView):
    model = Company
    template_name = 'companies/view.html'


class CompaniesDataView(LoginRequiredMixin, View):
    def get(self, request):
        companies = Company.objects.all()
        companies_list = []
        for item in companies:
            item_dict = {
                'id': item.id,
                'name': item.name,
                'app_ref': item.app_ref,
                'description': item.description,
                'logo': item.logo_url,
                'status': item.status,
                'country': item.country,
                'city': item.city,
                'telephone': item.telephone,
                'email': item.email,
                'actions': '<a href="/companies/' + str(item.id) + '" class="btn btn-primary btn-sm"><i class="mdi mdi-eye"></i> View</a>'
            }
            companies_list.append(item_dict)
        return JsonResponse({'data': companies_list})


class ContractAccessView(CreateView):
    model = UserContractAccess
    form_class = ContractAccessForm
    template_name = 'contracts/add_access.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['contract'] = self.kwargs.get('pk')
        return initial
    
    def get_success_url(self):
        return reverse_lazy('contracts-web:contract-details', kwargs={'pk': self.object.contract.pk})

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
    
    def form_invalid(self, form):
        return super().form_invalid(form)
