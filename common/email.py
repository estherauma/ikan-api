
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from enum import Enum
from decouple import config


class EmailTemplate(Enum):
    APPLICATION = 'application.html'


class TunaEmailHelper:

    @classmethod
    def send_plain_email(cls, subject, body, to_emails, from_email=config("APPLICATION_FROM_EMAIL"),):
        email = EmailMessage(subject=subject, body=body, from_email=from_email, to=to_emails)
        email.send()

    @classmethod
    def send_templated_email(cls, template, to_emails, subject, context, from_email=config("APPLICATION_FROM_EMAIL")):
        html_message = render_to_string(f'emails/{template}', context)
        plain_message = strip_tags(html_message)

        send_mail(subject, plain_message, from_email, to_emails, html_message=html_message)
