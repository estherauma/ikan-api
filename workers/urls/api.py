from django.urls import path
from workers.views.api import WorkerApiListView, WorkerApiDetailView

app_name = 'workers'

urlpatterns = [
  path('workers', WorkerApiListView.as_view(), name='worker-list'),
  path('workers/<int:id>', WorkerApiDetailView.as_view(), name='worker-detail'),
]
