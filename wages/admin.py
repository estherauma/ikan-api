from django.contrib import admin
from django import forms
from accounts.admin_utils import set_created_by_choices
from wages.models import Wage


class WageAdminForm(forms.ModelForm):
    created_by = forms.ChoiceField(required=False)

    class Meta:
        model = Wage
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_created_by_choices(self)


class WageAdmin(admin.ModelAdmin):
    form = WageAdminForm


admin.site.register(Wage, WageAdmin)
