from django.urls import path

from traders.views.web import (
    InviteTraderView,
    RemoveTraderVesselOwnerRelationshipView,
    ResendTraderInviteView,
    TraderDashboardOverviewView,
    TraderDashboardWagePaymentsView,
    TraderDetailView,
    TradersListView,
)

app_name = 'traders'

urlpatterns = [
    path('', TradersListView.as_view(), name='traders'),
    path('dashboard/', TraderDashboardOverviewView.as_view(), name='dashboard-overview'),
    path('dashboard/wage-payments/', TraderDashboardWagePaymentsView.as_view(), name='dashboard-wage-payments'),
    path('invite', InviteTraderView.as_view(), name='invite-trader'),
    path('resend-invite', ResendTraderInviteView.as_view(), name='resend-invite'),
    path('<pk>/', TraderDetailView.as_view(), name='details'),
    path(
        '<pk>/vessel-owner-relationships/<relationship_pk>/remove',
        RemoveTraderVesselOwnerRelationshipView.as_view(),
        name='remove-vessel-owner-relationship',
    ),
]
