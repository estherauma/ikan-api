from django.urls import path
from .views import (
    TunaTokenObtainPairView,
)
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('token', TunaTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh')
]
