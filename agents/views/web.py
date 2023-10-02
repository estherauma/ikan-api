from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from agents.models import Agent


class AgentsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'agents.html')


class AgentsDataView(LoginRequiredMixin, View):
    def get(self, request):
        agents = Agent.objects.all()
        agents_list = []
        for item in agents:
            agent = {
                "app_ref": item.app_ref,
                "name": item.name,
                "contact_name": item.contact_name,
                "email": item.email,
                "telephone": item.telephone,
                "logo_url": item.logo_url,
                "status": item.status,
                "country": item.country,
                "zip": item.zip,
                "town": item.town,
                "building_name": item.building_name,
                "road": item.road,
            }
            agents_list.append(agent)
        return JsonResponse({'data': agents_list})
