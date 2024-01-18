from django.urls import path
from vessels.views.web import VesselsView, VesselDetailView, VesselsDataView

app_name = 'vessels-web'
urlpatterns = [
    path('', VesselsView.as_view(), name='vessels'),
    path('data', VesselsDataView.as_view(), name='vessels-data'),
    path('<pk>/', VesselDetailView.as_view(), name='vessel-details'),
]
