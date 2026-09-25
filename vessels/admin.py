from django.contrib import admin
from django import forms
from vessels.models import Vessel, VesselImage


class VesselAdminForm(forms.ModelForm):
    class Meta:
        model = Vessel
        fields = '__all__'


class VesselAdmin(admin.ModelAdmin):
    form = VesselAdminForm


# Register your models here.
admin.site.register(Vessel, VesselAdmin)
admin.site.register(VesselImage)
