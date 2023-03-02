
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from enum import Enum
from decouple import config


class EmailType(Enum):
    APPLICATION = 'application_email'


def tuna_send_application_email(
    to_emails,
    position,
    name,
    company,
    from_email=config("APPLICATION_FROM_EMAIL"),
):
    subject = f'Call for Applications: {position} at {company}'
    context = {'name': name, 'position': position, 'company': company}
    html_message = render_to_string('emails/application.html', context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject,
        plain_message,
        from_email,
        to_emails,
        html_message=html_message
    )


def tuna_send_email(
    subject,
    body,
    to_emails,
    from_email=config("APPLICATION_FROM_EMAIL"),
):
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to_emails,
    )
    email.send()
