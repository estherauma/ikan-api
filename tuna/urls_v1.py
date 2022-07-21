from django.urls import path
from django.http import HttpResponse
from tuna.views import welcome

urlpatterns = [
    path('', welcome, name='welcome' ),
]
