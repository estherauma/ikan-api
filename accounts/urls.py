from django.urls import path
from .views import (
    LoginView,
)


urlpatterns = [
    # path('token/', TunaTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh')
    path('login/', LoginView.as_view(), name='login'),
]
