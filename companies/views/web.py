from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import BaseModelForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views import View
from companies.models import Company
from django.views import generic

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
