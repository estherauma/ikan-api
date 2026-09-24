from django.contrib import admin
from django import forms
from wages.models import Wage


class WageAdminForm(forms.ModelForm):
    class Meta:
        model = Wage
        fields = '__all__'


class WageAdmin(admin.ModelAdmin):
    form = WageAdminForm


admin.site.register(Wage, WageAdmin)
