from django.urls import path

from prismic.views import (
    AggregatedContentView,
    compare_content,
)

urlpatterns = [
    path('aggregated/', AggregatedContentView.as_view(), name='aggregated-content'),
    path('compare/', compare_content, name="compare_content"),
]
