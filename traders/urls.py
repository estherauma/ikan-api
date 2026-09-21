from django.urls import path

from traders.views.web import (
    InviteTraderView,
    RemoveTraderVesselOwnerRelationshipView,
    ResendTraderInviteView,
    TraderDetailView,
    TradersListView,
)

app_name = 'traders'

urlpatterns = [
    path('', TradersListView.as_view(), name='traders'),
    path('invite', InviteTraderView.as_view(), name='invite-trader'),
    path('resend-invite', ResendTraderInviteView.as_view(), name='resend-invite'),
    path('<pk>/', TraderDetailView.as_view(), name='details'),
    path(
        '<pk>/vessel-owner-relationships/<relationship_pk>/remove',
        RemoveTraderVesselOwnerRelationshipView.as_view(),
        name='remove-vessel-owner-relationship',
    ),
]
