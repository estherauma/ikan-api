from django.conf.urls import include
from django.urls import path
from django.http import HttpResponse
from tuna.views import welcome, sample_data

urlpatterns = [
    path('', welcome, name='welcome' ),
    path('renderers/', sample_data, name='sample'),
    path('content/', include('prismic.urls'))
]
