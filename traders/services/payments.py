from accounts.models import TraderVesselOwnerRelationship
from django.db.models import Q
from vessels.models import Vessel
from wages.models import Wage


WAGE_STATUS_SUMMARY = {
    'received': {
        'label_key': 'recievedFull',
        'color': '#65E878',
    },
    'issue_pending': {
        'label_key': 'issuesReported',
        'color': '#F44E5E',
    },
    'action_required': {
        'label_key': 'pendingCrewReview',
        'color': '#FF9824',
    },
}


class WagePaymentsService:
    def __init__(self, trader, dashboard_text=None):
        self.trader = trader
        self.dashboard_text = dashboard_text or {}

    def get_text(self, key):
        return self.dashboard_text.get(key) or key

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
            label = self.get_text(config['label_key'])
            item = {
                'label': label,
                'percent': percent,
                'color': config['color'],
            }
            legend.append(item)
            chart_segments.append({
                'label': label,
                'percent': percent,
                'color': config['color'],
            })

        return {
            'title': self.get_text('totalPaymentCompletion'),
            'completed_percent': legend[0]['percent'],
            'completed_label': self.get_text('completed'),
            'chart_segments': chart_segments,
            'legend': legend,
        }

    def get_payment_summary(self, wages=None):
        return {
            'completion': self.get_payment_completion_summary(wages),
            'metric_groups': [
                self.get_payslip_status_summary(wages),
            ],
        }

    def get_payslip_status_summary(self, wages=None):
        if wages is None:
            wages = self.get_wages_queryset()

        total_wages = wages.count()
        signed_filter = Q(payslip_status=Wage.PAYSLIP_STATUS_SIGNED)
        no_payslip_filter = Q(payslip__isnull=True) | Q(payslip='')
        signature_pending_filter = ~signed_filter & ~no_payslip_filter

        signed_count = wages.filter(signed_filter).count()
        no_payslip_count = wages.filter(no_payslip_filter).count()
        signature_pending_count = wages.filter(signature_pending_filter).count()

        return {
            'title': self.get_text('payslipStatus'),
            'items': [
                {
                    'label': self.get_text('signed'),
                    'percent': self.get_percent(signed_count, total_wages),
                    'color': '#65E878',
                },
                {
                    'label': self.get_text('signaturePending'),
                    'percent': self.get_percent(signature_pending_count, total_wages),
                    'color': '#FF9824',
                },
                {
                    'label': self.get_text('noPayslip'),
                    'percent': self.get_percent(no_payslip_count, total_wages),
                    'color': '#F44E5E',
                },
            ],
        }

    def get_percent(self, count, total):
        return round((count / total) * 100) if total else 0

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
                'status': (
                    self.get_text('nonCompliant')
                    if has_issues else self.get_text('noIssues')
                ),
                'status_value': 'non_compliant' if has_issues else 'no_issues',
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
        vessel_summary = ', '.join(vessel_names) if vessel_names else self.get_text('noVessels')
        crew_count = wages.values('user_id').distinct().count()
        return f'{vessel_summary} | {crew_count} {self.get_text("crew")}'

    def get_user_display_name(self, user):
        full_name = f'{user.first_name} {user.last_name}'.strip()
        return full_name or user.email or user.mobile or user.telephone or str(user.pk)

    def format_payslip_row(self, wage):
        status = self.get_text('noPayslip')
        status_class = 'no-payslip'
        attachment_url = None

        if wage.payslip_status == Wage.PAYSLIP_STATUS_SIGNED:
            status = self.get_text('signed')
            status_class = 'signed'
        elif wage.payslip:
            status = self.get_text('signaturePending')
            status_class = 'pending'

        if wage.payslip:
            attachment_url = wage.payslip.url

        return {
            'worker_name': self.get_user_display_name(wage.user),
            'role': wage.user.position or '',
            'amount': f'US$ {wage.usd_amount:,.2f}',
            'status': status,
            'status_class': status_class,
            'attachment_url': attachment_url,
        }
