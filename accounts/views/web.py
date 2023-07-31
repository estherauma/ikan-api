from django.shortcuts import render


def get_base(request):
    return render(request, template_name="themes/v1/base.html")

def login(request):
    return render(request, template_name="login.html")

def request_password_reset(request):
    return render(request, template_name='password-reset/request-password-reset.html')

def reset_password(request):
    return render(request, template_name='password-reset/reset-password.html')
