from django.views import View
from django.shortcuts import render

# Create your views here.
class VesselOwnerDashboard(View):
    def get(self, request):
        context = {'page_title': 'Vessel Owner Dashboard'}
        return render(request, 'vessel_owner.html', context)
    

class BuyerDashboard(View):
    def get(self, request):
        context = {'page_title': 'Buyer Dashboard'}
        return render(request, 'buyer.html', context)


class WorkerDashboard(View):
    def get(self, request):
        context = {'page_title': 'Worker Dashboard'}
        return render(request, 'worker.html', context)
    
class AgentDashboard(View):
    def get(self, request):
        context = {'page_title': 'Agent Dashboard'}
        return render(request, 'agent.html', context)
    