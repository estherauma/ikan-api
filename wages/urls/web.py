from django.urls import path
from wages.views.web import (
    WageListView,
    WageDetailView,
    AddWagesView,
    SelectVesselView
)

app_name = "wages"

urlpatterns = [
    path("", WageListView.as_view(), name="wages-list"),
    path("<pk>/", WageDetailView.as_view(), name="wage-details"),
    path("select-vessel", SelectVesselView.as_view(), name='select-vessel'),
    path("add-wages", AddWagesView.as_view(), name="add-wages"),
]
