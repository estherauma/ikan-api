from django.urls import path
from mydocuments.views.api import DocumentApiListView, PassportApiListView, \
    DocumentApiDetailView, PassportApiDetailView

app_name = 'mydocuments'

urlpatterns = [
    path('mydocuments', DocumentApiListView.as_view(), name='document-list'),
    path('mydocuments/<str:id>', DocumentApiDetailView.as_view(), name='document-detail'),
    path('passports', PassportApiListView.as_view(), name='passport-list'),
    path('passports/<str:id>', PassportApiDetailView.as_view(), name='passport-detail')
]
