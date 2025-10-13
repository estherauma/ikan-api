from django import forms
from vessels.models import Vessel
from wages.models import Wage
from django.forms import modelformset_factory, BaseModelFormSet
from django.core.exceptions import ValidationError
from wages.utils import (
    wage_fields,
    get_workers_on_vessel,
)


class VesselSelectForm(forms.Form):
    vessel = forms.ModelChoiceField(
        queryset=Vessel.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                "placeholder": "Select Vessel",
                "style": "min-height: 45px; border-radius: 10px; border-width: 1px; min-width: 200px;\
                    max-width: 500px; padding: 0 10px; font-size: 1.1rem;",
                "id": "vessel-select",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["vessel"].queryset = Vessel.objects.filter(created_by=user.id)
