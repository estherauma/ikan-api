from django import forms
from vessels.models import Vessel


class UploadPaymentsForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'file',
            'accept': '.xlsx, .xls',
        }),
        label='',
    )


class VesselSelectForm(forms.Form):
    vessel = forms.ModelChoiceField(
        queryset=Vessel.objects.none(),
        required=True,
        widget=forms.Select(
            attrs={
                'placeholder': 'Select Vessel',
                'style': 'min-height: 45px; border-radius: 10px; border-width: 1px; min-width: 300px; \
                    max-width: 500px; padding: 0 10px; font-size: 1.1rem;',
                'id': 'vessel-select',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['vessel'].queryset = Vessel.objects.filter(created_by=user.id)
