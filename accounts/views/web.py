from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.list import ListView
from accounts.forms import RegistrationForm

# models
from accounts.models import User


def get_base(request):
    return render(request, template_name="themes/v1/base.html")


def login(request):
    return render(request, template_name="login.html")


def request_password_reset(request):
    return render(request, template_name='password-reset/request-password-reset.html')


def reset_password(request):
    return render(request, template_name='password-reset/reset-password.html')


class UserListView(ListView):
    model = User
    context_object_name = 'users'
    template_name = 'user-list.html'


def reg(request):
    return render(request, template_name='register.html')


class RegisterWebView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'register.html', {'form': form})

    def post(self, request):
        form = RegistrationForm(data=request.POST)

        if not form.is_valid():
            return render(request, 'register.html', {'form': form})
        else:
            user = User.objects.create_user(
                email=form.cleaned_data.get('email'),
                password=form.cleaned_data.get('password'),
                first_name=form.cleaned_data.get('first_name'),
                last_name=form.cleaned_data.get('last_name'),
                is_active=False
            )

        return redirect('/account/login')
