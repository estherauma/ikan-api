from django import forms


class UploadPaymentsForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'file',
            'accept': '.csv',
        }),
        label='',
    )
