from django.urls import path
from .views import (
    LoginView,
    TestEmail,
)


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('test-email', TestEmail.as_view(), name='test-email')
]
