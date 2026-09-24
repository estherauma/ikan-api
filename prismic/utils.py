from django import forms
from decouple import config

from content.utils import ContentUtils
from prismic.models import AggregatedContent


use_strapi_content = config(
    "USE_STRAPI_CONTENT",
    default=False,
    cast=bool,
)


if use_strapi_content:
    PrismicUtils = ContentUtils
else:
    class PrismicUtils:
        def __init__(self, request):
            self.user = request.user
            self.is_superuser = self.user.is_superuser
            selected_lang = request.session.get('language', None)
            self.language = selected_lang if selected_lang else 'en-us'
            self.all_aggregated_content = self.get_all_aggregated_content()
            self.content = self.get_content()  # for selected language
            self.common_text = self.get_common_text()

        def get_all_aggregated_content(self):
            all_data = AggregatedContent.objects.all()
            latest_data = all_data.order_by('-created_at').first()
            if latest_data and latest_data.content:
                return latest_data.content
            return None

        def get_content(self):
            agg_content = self.all_aggregated_content
            if agg_content:
                return agg_content[self.language]
            return None

        def get_content_by_property_name(self, property_name):
            content = self.get_content()
            if content and property_name in content:
                return content[property_name]
            return None

        def get_page_title(self, property_name):
            page_data = self.get_content_by_property_name(property_name)
            if page_data and 'page_title' in page_data:
                return page_data['page_title']
            return None

        def get_form_questions(self, property_name):
            page_data = self.get_content_by_property_name(property_name)
            if page_data and 'form_questions' in page_data:
                return page_data['form_questions']
            return None

        def create_form(self, form_questions):
            class Form(forms.Form):
                def __init__(self, *args, **kwargs):
                    super(Form, self).__init__(*args, **kwargs)
                    if self.initial and self.initial.get('clause_kind'):
                        if self.initial['clause_kind'] == 'contract-clauses-attachments':
                            if self.initial.get('partyASignature'):
                                self.fields['partyASignature'].required = False
                            if self.initial.get('partyBSignature'):
                                self.fields['partyBSignature'].required = False

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

                select_option_text = self.common_text.get('selectOption', 'Select option')

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
                        choices=[('', select_option_text)]+[(option['value'], option['label']) for option in options],
                        widget=forms.Select(attrs={'placeholder': placeholder, 'class': 'form-control ikan-select'})
                    )
                elif field_type == 'multiple-select' or field_type == 'multi-select':
                    field = forms.MultipleChoiceField(
                        label=label,
                        required=required,
                        help_text=help_text,
                        # TODO: add translation for placeholder when langiage switching is implemented
                        choices=[('', select_option_text)]+[(option['value'], option['label']) for option in options],
                        widget=forms.SelectMultiple(attrs={'placeholder': placeholder, 'class': 'form-control ikan-select'})
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
            return option_value

        def get_field_labels_from_form_questions(self, form_questions, property_name=None):
            """
            Get field labels from form questions.
            If no form questions but the property name is provided,
            use property name to get the form questions and in turn field the labels.

            Usage:
                get_field_labels_from_form_questions(form_questions)
                get_field_labels_from_form_questions(None, property_name)
            Example:
                get_field_labels_from_form_questions(profile_form_questions)
                get_field_labels_from_form_questions(None, profile_property_name)
            """
            if not form_questions and property_name:
                form_questions = self.get_form_questions(property_name)

            labels = {}
            if form_questions:
                for qtn in form_questions:
                    if qtn['label']:
                        labels[qtn['key']] = qtn['label']

            return labels

        def get_common_text(self):
            if not self.content:
                return {}
            common_text = {}
            common_content = self.content.get('commonText', None)
            if common_content and 'data' in common_content:
                for item in common_content['data']:
                    common_text[item['label']] = item['value']
            return common_text

        def get_page_text(self, property_name):
            page_data = self.get_content_by_property_name(property_name)

            page_text = {}
            if page_data and 'additional_text' in page_data and page_data['additional_text']:
                for item in page_data['additional_text']:
                    page_text[item['label']] = item['value']
            return page_text

        def get_menu_content(self):
            pass

        def get_menu_labels(self):
            menu_labels = {}
            menu_data = self.get_content_by_property_name('sidemenu')
            if menu_data and 'data' in menu_data:
                for item in menu_data['data']:
                    menu_labels[item['key']] = item['label']

                menu_labels['home'] = menu_labels.get('workerDashboard', menu_labels.get('vesselownerDashboard', 'Home'))
            return menu_labels
