from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from vessels.models import Vessel


class VesselsView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'vessels/list.html')

class VesselDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        vessel = Vessel.objects.get(id=id)
        return render(request, 'vessels/view.html', {'vessel': vessel})

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
                'actions': '<a href="/vessels/view/' + str(item.id) + '" class="btn btn-primary btn-sm"><i class="mdi mdi-eye"></i> View</a>  <a href="/vessels/edit/' + str(item.id) + '" class="btn btn-primary btn-sm"><i class="mdi mdi-pen"></i> Edit</a>'
            }
            vessels_list.append(vessel)
        return JsonResponse({'data': vessels_list})
