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

