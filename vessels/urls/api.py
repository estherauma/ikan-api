from django.urls import path
from vessels.views.api import VesselApiListView, VesselImageApiListView, \
    VesselApiDetailView, VesselImageApiDetailListView


app_name = 'vessels'

urlpatterns = [
    path('vessels', VesselApiListView.as_view(), name='vessel-list'),
    path('vessels/<str:id>', VesselApiDetailView.as_view(), name='vessel-detail'),
    path('vessels-images', VesselImageApiListView.as_view(), name='vessel-images-list'),
    path('vessels-images/<str:id>', VesselImageApiDetailListView.as_view(), name='vessel-image-detail')
]
