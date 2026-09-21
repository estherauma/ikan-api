from django.contrib import admin
from django import forms
from accounts.admin_utils import set_created_by_choices
from vessels.models import Vessel, VesselImage


class VesselAdminForm(forms.ModelForm):
    created_by = forms.ChoiceField(required=False)

    class Meta:
        model = Vessel
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_created_by_choices(self)


class VesselAdmin(admin.ModelAdmin):
    form = VesselAdminForm


# Register your models here.
admin.site.register(Vessel, VesselAdmin)
admin.site.register(VesselImage)
