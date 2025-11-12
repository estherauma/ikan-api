from django.urls import path
from wages.views.api import WageApiListView, WageApiDetailView

app_name = 'api-wages'

urlpatterns = [
    path('wages', WageApiListView.as_view(), name='wages-list'),
    path('wages/<id>', WageApiDetailView.as_view(), name='wage-detail'),
]
