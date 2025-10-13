from contracts.models import ContractClause
import json
from django.db.models import Q
from accounts.models import User
from django.utils.timezone import now


# IMPORTANT: Do not change the order of the fields in this list.
# These are the fields displayed in the form
# Editing this list will affect the fields displayed in the form
wage_fields = [
    "user",
    "payment_date",
    "start_date",
    "end_date",
    "usd_amount",
    "payslip",
    "crew_bank_transfer_receipt",
    "beneficiary_bank_transfer_receipt",
    "beneficiary_relationship",
    "beneficiary_name",
    "beneficiary_contact",
    "beneficiary_contact_platform",
]


def get_workers_on_vessel(vessel):
    contracts_with_vessel = []
    party_b_clauses = ContractClause.objects.filter(kind='contract-clauses-parties-requirement-fishers')
    for clause in party_b_clauses:
        try:
            content = json.loads(clause.content)
            if content.get('vessel') == vessel.app_ref:
                contracts_with_vessel.append(clause.contract)
        except (KeyError, json.JSONDecodeError):
            continue

    workers_on_vessel = User.objects.filter(
            Q(groups__name="worker") &
            Q(user_contract_access__contract__in=contracts_with_vessel)
        ).distinct()
    return workers_on_vessel


