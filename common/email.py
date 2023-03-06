
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from enum import Enum
from decouple import config


class EmailTemplate(Enum):
    APPLICATION = 'application.html'


class TunaEmailHelper:

    @classmethod
    def tuna_send_email(cls, to_emails, subject, body, template=None, from_email=config("APPLICATION_FROM_EMAIL")):

        if template is None:
            print('sent without template')
            return send_mail(subject, body, from_email, to_emails)
        
        print('** sent with template')
        html_message = render_to_string(f'emails/{template}', {"body": body})
        plain_message = strip_tags(html_message)

        send_mail(subject, plain_message, from_email, to_emails, html_message=html_message)
