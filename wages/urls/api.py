from django.urls import path
from wages.views.api import WageApiListView

app_name = 'api-wages'

urlpatterns = [
    path('wages/', WageApiListView.as_view(), name='wages-list'),
    path('wages/<pk>/', WageApiListView.as_view(), name='wage-detail'),
]
