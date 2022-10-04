from django.conf.urls import include
from django.urls import path
from tuna.views import (
    welcome,
    sample_data,
    health,
)

urlpatterns = [
    path('', welcome, name='welcome'),
    path('health/', health, name="health"),
    path('renderers/', sample_data, name='sample'),
    path('content/', include('prismic.urls'))
]
