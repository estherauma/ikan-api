from accounts.models import TraderVesselOwnerRelationship
from vessels.models import Vessel
from wages.models import Wage


WAGE_STATUS_SUMMARY = {
    'received': {
        'label': 'Received in full',
        'color': '#65E878',
    },
    'issue_pending': {
        'label': 'Issues reported',
        'color': '#F44E5E',
    },
    'action_required': {
        'label': 'Pending crew review',
        'color': '#FF9824',
    },
}


class WagePaymentsService:
    def __init__(self, trader):
        self.trader = trader

    def get_attached_vessel_owner_ids(self):
        return [
            str(vessel_owner_id)
            for vessel_owner_id in TraderVesselOwnerRelationship.objects.filter(
                trader=self.trader,
            ).values_list('vessel_owner_id', flat=True)
        ]

    def get_wages_queryset(self):
        vessel_owner_ids = self.get_attached_vessel_owner_ids()
        vessels = Vessel.objects.filter(created_by__in=vessel_owner_ids)
        return Wage.objects.filter(vessel__in=vessels).select_related('vessel', 'user')

    def get_payment_completion_summary(self):
        wages = self.get_wages_queryset()
        total_wages = wages.count()
        legend = []
        chart_segments = []

        for status, config in WAGE_STATUS_SUMMARY.items():
            count = wages.filter(status=status).count()
            percent = round((count / total_wages) * 100) if total_wages else 0
            item = {
                'label': config['label'],
                'percent': percent,
                'color': config['color'],
            }
            legend.append(item)
            chart_segments.append({
                'label': config['label'],
                'percent': percent,
                'color': config['color'],
            })

        return {
            'title': 'Total payment completion',
            'completed_percent': legend[0]['percent'],
            'completed_label': 'Completed',
            'chart_segments': chart_segments,
            'legend': legend,
        }
