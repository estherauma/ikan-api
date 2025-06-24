from prismic.models import AggregatedContent
from django import forms


class PrismicUtils:
    def __init__(self, request):
        self.user = request.user
        self.is_superuser = self.user.is_superuser
        # TODO: use selected language after implementing localization
        self.language = 'en-us'
        self.aggregated_content = None

    def get_content(self):
        all_data = AggregatedContent.objects.all()
        recent_data = all_data.order_by('-created_at').first()
        if recent_data and recent_data.content:
            return recent_data.content[self.language]
        return None

    def get_content_by_property_name(self, property_name):
        content = self.get_content()
        if content and property_name in content:
            return content[property_name]
        return None

    def get_form_questions(self, property_name):
        page_data = self.get_content_by_property_name(property_name)
        if page_data and 'form_questions' in page_data:
            return page_data['form_questions']
        return None

    def create_form(self, form_questions):
        class Form(forms.Form):
            pass

        for question in form_questions:
            if not question.get('displayquestion', True):
                continue  # Skip questions that are not to be displayed

            key = question["key"]
            label = question["label"]
            required = question["is_required"] if question['is_required'] is not None else False
            help_text = question.get("help_text", "") if question.get("help_text") else ""
            placeholder = question.get("placeholder", "") if question.get("placeholder") else ""
            field_type = question["question_type"]
            options = question.get("options", [])

            if field_type == 'textBox' or field_type == 'text':
                field = forms.CharField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.TextInput(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            elif field_type == 'textArea' or field_type == 'textarea':
                field = forms.CharField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.Textarea(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            elif field_type == 'select':
                field = forms.ChoiceField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    # TODO: add translation for placeholder when language switching is implemented
                    choices=[('', 'Select option')]+[(option['value'], option['label']) for option in options],
                    widget=forms.Select(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            elif field_type == 'multiple-select' or field_type == 'multi-select':
                field = forms.MultipleChoiceField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    # TODO: add translation for placeholder when langiage switching is implemented
                    choices=[('', 'Select options')]+[(option['value'], option['label']) for option in options],
                    widget=forms.SelectMultiple(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            elif field_type == 'tel' or field_type == 'telephone':
                field = forms.CharField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.TextInput(attrs={'placeholder': placeholder, 'type': 'tel', 'class': 'form-control'})
                )
            elif field_type == 'email':
                field = forms.EmailField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.EmailInput(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            elif field_type == 'number':
                field = forms.IntegerField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.NumberInput(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            elif field_type == 'checkbox':
                field = forms.BooleanField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.CheckboxInput(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            # TODO: separate file, imageBox and pdfDocument field types
            elif field_type == 'file' or field_type == 'imageBox' or field_type == 'pdfDocument':
                field = forms.FileField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.ClearableFileInput(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            elif field_type == 'date':
                field = forms.DateField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.DateInput(attrs={'placeholder': placeholder, 'type': 'date', 'class': 'form-control'}),
                    # input_formats=['%Y-%m-%d']
                )
            elif field_type == 'radio' or field_type == 'radioGroup':
                field = forms.ChoiceField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    choices=[(option['value'], option['label']) for option in options],
                    widget=forms.RadioSelect(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )
            # Add more field types here
            else:
                field = forms.CharField(
                    label=label,
                    required=required,
                    help_text=help_text,
                    widget=forms.TextInput(attrs={'placeholder': placeholder, 'class': 'form-control'})
                )

            Form.base_fields[key] = field

        return Form

    def get_question_options(self, property_name, question_key):
        """
        Get the options for a specific question based on the property name and question key.
        """
        form_questions = self.get_form_questions(property_name)
        if form_questions:
            question = next((q for q in form_questions if q['key'] == question_key), None)
            return question['options'] if question['options'] else None
        return None

    def get_question_option_translation(self, property_name, question_key, option_value):
        """
        Get the translated value for a form option based on the property name and question key.
        """
        options = self.get_question_options(property_name, question_key)
        if not options:
            return option_value  # Return the original value if no options found

        option = next((opt for opt in options if opt['value'] == option_value), None)
        if option:
            return option.get('label', option_value)
        return option['label'] if option['label'] else option_value
