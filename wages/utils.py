from contracts.models import ContractClause
import json
from django.db.models import Q
from accounts.models import User


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
    # This field is temporarily disabled/removed from the form
    # "beneficiary_contact_platform",
]


file_fields = [
    "payslip",
    "crew_bank_transfer_receipt",
    "beneficiary_bank_transfer_receipt",
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


def generate_wage_field_labels(payments_common_text):
    return {
        "user": payments_common_text.get("crewName", "Crew Name"),
        "payment_date": payments_common_text.get("paymentDate", "Payment Date"),
        "start_date": payments_common_text.get("startDate", "Start Date"),
        "end_date": payments_common_text.get("endDate", "End Date"),
        "usd_amount":
            f'{payments_common_text.get("totalAmount", "Total amount")} {payments_common_text.get("USD", "USD")}',
        "payslip": payments_common_text.get("payslip", "Payslip"),
        "crew_bank_transfer_receipt": payments_common_text.get("crewBankTransferReceipt", "Crew Bank Transfer Receipt"),
        "beneficiary_bank_transfer_receipt": payments_common_text.get("beneficiaryBankTransferReceipt",
                                                                      "Beneficiary Bank Transfer Receipt"),
        "beneficiary_relationship": payments_common_text.get("beneficiaryRelationship", "Beneficiary Relationship"),
        "beneficiary_name": payments_common_text.get("beneficiaryName", "Beneficiary Name"),
        "beneficiary_contact": payments_common_text.get("beneficiaryContact", "Beneficiary Contact"),
        "beneficiary_contact_platform": payments_common_text.get("beneficiaryContactPlatform",
                                                                 "Beneficiary Contact Platform"),
    }


def generate_beneficiary_relationship_options(payments_common_text):
    return [
        {"key": "self", "label": payments_common_text.get("crewMemberHimself", "Crew member himself")},
        {"key": "family_or_friend", "label": payments_common_text.get("familyOrFriend", "Family/friend")},
        {"key": "crew_member_and_family_or_friend", "label": payments_common_text.get("crewMemberAndFamilyOrFriend",
                                                                                      "Crew member and family/friend")},
    ]


def get_status_label(status, payments_common_text, is_vessel_owner=False):
    label = payments_common_text.get("unknown", "Unknown")
    status_class = "unknown"
    if is_vessel_owner:
        if status == "action_required" or status == "issue_pending":
            label = payments_common_text.get("pending", "Pending")
            status_class = "pending"
        elif status == "received":
            label = payments_common_text.get("confirmed", "Confirmed")
            status_class = "confirmed"
    else:
        if status == "action_required":
            label = payments_common_text.get("actionRequired", "Action Required")
            status_class = "action-required"
        elif status == "issue_pending":
            label = payments_common_text.get("issuePending", "Issue Pending")
            status_class = "issue-pending"
        elif status == "received":
            label = payments_common_text.get("received", "Received")
            status_class = "received"

    return {"label": label, "class": status_class}
