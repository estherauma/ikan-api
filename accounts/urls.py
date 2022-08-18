from django.urls import path
from .views import (
    TunaTokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
    path('token', TunaTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh')
]
