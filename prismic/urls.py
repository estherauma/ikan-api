from django.urls import path

from prismic.views import (
    AggregatedContentView,
    UpdatedContentView
    )

urlpatterns = [
    path('aggregated', AggregatedContentView.as_view(), name='aggregated-content'),
    path('updated', UpdatedContentView.as_view(), name='updated-content', )
]
