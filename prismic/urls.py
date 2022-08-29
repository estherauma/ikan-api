from django.urls import path

from prismic.views import AggregatedContentView

urlpatterns = [
    path('aggregated', AggregatedContentView.as_view(), name='aggregated-content')
]
