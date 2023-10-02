from django.urls import path
from vessels.views.api import VesselApiListView, VesselImageApiListView,\
  VesselApiDetailView, VesselImageApiDetailListView


app_name = 'vessels'

urlpatterns = [
    path('vessels', VesselApiListView.as_view(), name='vessel-list'),
    path('vessels/<int:pk>', VesselApiDetailView.as_view(), name='vessel-detail'),
    path('vessels/images', VesselImageApiListView.as_view(), name='vessel-detail-list'),
    path('vessels/images/<int:pk>', VesselImageApiDetailListView.as_view(), name='vessel-detail-detail')
]
