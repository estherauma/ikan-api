from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from organizations.models import Organization


class OrganizationsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'organizations.html')
    
class OrganizationDataView(LoginRequiredMixin, View):
    def get(self, request):
        organizations = Organization.objects.all()
        organizations_list = []
        for organization in organizations:
            organization_dict = {
                'id': organization.id,
                'name': organization.name,
                'app_ref': organization.app_ref,
                'description': organization.description,
                'logo': organization.logo,
                'status': organization.status,
                'country': organization.country,
                'city': organization.city,
                'telephone': organization.telephone,
                'email': organization.email
            }
            organizations_list.append(organization_dict)
        return JsonResponse({'data': organizations_list})