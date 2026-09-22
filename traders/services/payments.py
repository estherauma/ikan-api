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


PAYMENT_METRIC_GROUPS = [
    {
        'title': 'Payslip status',
        'items': [
            {'label': 'Signed', 'percent': 77, 'color': '#65E878'},
            {'label': 'Signature pending', 'percent': 20, 'color': '#FF9824'},
            {'label': 'No payslip', 'percent': 3, 'color': '#F44E5E'},
        ],
    },
]


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

    def get_vessels_for_vessel_owner_ids(self, vessel_owner_ids):
        vessels = Vessel.objects.filter(created_by__in=vessel_owner_ids)
        return vessels

    def get_vessels_for_vessel_owner(self, vessel_owner):
        return self.get_vessels_for_vessel_owner_ids([str(vessel_owner.pk)])

    def get_wages_for_vessels(self, vessels):
        return Wage.objects.filter(vessel__in=vessels).select_related('vessel', 'user')

    def get_wages_queryset(self):
        vessel_owner_ids = self.get_attached_vessel_owner_ids()
        vessels = self.get_vessels_for_vessel_owner_ids(vessel_owner_ids)
        return self.get_wages_for_vessels(vessels)

    def get_payment_completion_summary(self, wages=None):
        if wages is None:
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

    def get_payment_summary(self, wages=None):
        return {
            'completion': self.get_payment_completion_summary(wages),
            'metric_groups': PAYMENT_METRIC_GROUPS,
        }

    def get_supplier_rows(self):
        relationships = TraderVesselOwnerRelationship.objects.filter(
            trader=self.trader,
        ).select_related('vessel_owner')

        supplier_rows = []
        for relationship in relationships:
            vessel_owner = relationship.vessel_owner
            vessels = self.get_vessels_for_vessel_owner(vessel_owner)
            vessel_names = list(vessels.values_list('name', flat=True))
            wages = self.get_wages_for_vessels(vessels)
            has_issues = wages.filter(status='issue_pending').exists()

            supplier_rows.append({
                'name': self.get_user_display_name(vessel_owner),
                'summary': self.get_supplier_summary(vessel_names, wages),
                'status': 'Non-compliant' if has_issues else 'No issues',
                'status_class': 'danger' if has_issues else 'good',
                'is_expanded': False,
                'payslip_count': wages.count(),
                'payment_summary': self.get_payment_summary(wages),
                'payslips': [
                    self.format_payslip_row(wage)
                    for wage in wages
                ],
            })

        return supplier_rows

    def get_supplier_summary(self, vessel_names, wages):
        vessel_summary = ', '.join(vessel_names) if vessel_names else 'No vessels'
        crew_count = wages.values('user_id').distinct().count()
        return f'{vessel_summary} | {crew_count} CREW'

    def get_user_display_name(self, user):
        full_name = f'{user.first_name} {user.last_name}'.strip()
        return full_name or user.email or user.mobile or user.telephone or str(user.pk)

    def format_payslip_row(self, wage):
        is_received = wage.status == 'received'
        return {
            'worker_name': self.get_user_display_name(wage.user),
            'role': wage.user.position or '',
            'amount': f'US$ {wage.usd_amount:,.2f}',
            'status': 'Submitted confirmation' if is_received else 'Pending review/signature on payslip',
            'status_class': 'submitted' if is_received else 'pending',
        }
