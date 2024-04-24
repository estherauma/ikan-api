from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from vessels.models import Vessel
from django.views import generic


class VesselsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'vessels/list.html')


class VesselDetailView(LoginRequiredMixin, generic.DetailView):
    model = Vessel
    template_name = 'vessels/view.html'


class VesselsDataView(LoginRequiredMixin, View):
    def get(self, request):
        super_user = self.request.user.is_superuser
        vessels = Vessel.objects.all() if super_user else Vessel.objects.filter(created_by=request.user.id)
        vessels_list = []
        for item in vessels:
            vessel = {
                "app_ref": item.app_ref,
                "name": item.name,
                "reg_no": item.reg_no,
                "vessel_type": item.vessel_type,
                "status": item.status,
                "capacity": item.capacity,
                "commissioning_date": item.commissioning_date,
                'actions': '<a href="/vessels/' + str(item.id) + '" class="btn btn-primary btn-sm"><i class="mdi mdi-eye"></i> View</a>'
            }
            vessels_list.append(vessel)
        return JsonResponse({'data': vessels_list})
