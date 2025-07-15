from contracts.models import ContractClause
import json
from django.db.models import Q
from accounts.models import User
from django.utils.timezone import now


methods_map = {
    "cash": "現金 Cash",
    "bank_transfer": "匯款 Bank Transfer",
    "both": "两个都 Both",
}

initial_required_fields = [
    "user",
    "payment_date",
    "payment_category",
    "payment_method",
    "start_date",
    "end_date",
    "total_usd_amount_received",
]

cash_fields = [
    "cash_amount",
    "cash_currency",
    "cash_exchange_rate",
    "cash_beneficiary_relationship",
    "cash_beneficiary_contact",
    "cash_beneficiary_name",
]

cash_beneficiary_fields = [
    "cash_beneficiary_name",
    "cash_beneficiary_contact",
]

bank_transfer_fields = [
    "bank_transfer_amount",
    "bank_transfer_currency",
    "bank_transfer_exchange_rate",
    "bank_account_name",
    "bank_account_number",
    "bank_name",
    "bank_transfer_beneficiary_relationship",
    "bank_transfer_beneficiary_name",
    "bank_transfer_beneficiary_contact",
]

deduction_fields = [
    "has_deductions",
    "add_deduction",
    "view_deductions",
    "deductions",
]

bank_transfer_beneficiary_fields = [
    "bank_transfer_beneficiary_name",
    "bank_transfer_beneficiary_contact",
]

beneficiaries_map = {
    "self": "船員自己 Crew member himself",
    "family_or_friend": "家人/朋友 Family/friend",
}


# IMPORTANT: Do not change the order of the fields in this list.
# These are the fields displayed in the form
# Editing this list will affect the fields displayed in the form
payment_fields = [
    "user",
    "payment_date",
    "payment_category",
    "start_date",
    "end_date",
    "total_usd_amount_received",
    "payment_method",
    "cash_amount",
    "cash_currency",
    "cash_exchange_rate",
    "cash_beneficiary_relationship",
    "cash_beneficiary_name",
    "cash_beneficiary_contact",
    "bank_transfer_amount",
    "bank_transfer_currency",
    "bank_transfer_exchange_rate",
    "bank_account_name",
    "bank_account_number",
    "bank_name",
    "bank_transfer_beneficiary_relationship",
    "bank_transfer_beneficiary_name",
    "bank_transfer_beneficiary_contact",
    # "has_deductions",  # temporarily removed. Uncomment to display. Also uncomment field in forms.py
    "deductions",
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


def get_formset_initial_values(vessel):
    initial_data = []

    workers_on_vessel = get_workers_on_vessel(vessel)
    for worker in workers_on_vessel:
        worker_initial_data = {
            "user": str(worker),
            "user_id": worker.id,
            "payment_date": str(now().date()),
            "payment_category": None,
            "start_date": None,
            "end_date": None,
            "total_usd_amount_received": None,
            "payment_method": None,
            "cash_amount": None,
            "cash_currency": None,
            "cash_exchange_rate": None,
            "cash_beneficiary_relationship": None,
            "cash_beneficiary_name": None,
            "cash_beneficiary_contact": None,
            "bank_transfer_amount": None,
            "bank_transfer_currency": None,
            "bank_transfer_exchange_rate": None,
            "bank_account_name": None,
            "bank_account_number": None,
            "bank_name": None,
            "bank_transfer_beneficiary_relationship": None,
            "bank_transfer_beneficiary_name": None,
            "bank_transfer_beneficiary_contact": None,
            "monthly_wage": None,  # to be used to calculate wages for entered work period
        }
        worker_contract_clauses = ContractClause.objects.filter(contract__contract_user_access__user=worker)

        wage_benefits_clause = None
        has_wage_benefits_clause = worker_contract_clauses.filter(kind="contract-clauses-wage-benefits").exists()
        if has_wage_benefits_clause:
            wage_benefits_clause = worker_contract_clauses.filter(kind="contract-clauses-wage-benefits").first()
            wage_benefits = json.loads(wage_benefits_clause.content)
            worker_initial_data["monthly_wage"] = wage_benefits.get("monthlyWage")
            # TODO: get add cash and bank transfer amounts and beneficiary details when
            # implemented (data is captured when creating clause).

        attachments_content = {}
        party_b_content = {}
        has_attachments_clause = worker_contract_clauses.filter(kind="contract-clauses-attachments").exists()
        has_party_b_clause = worker_contract_clauses.filter(
            kind="contract-clauses-parties-requirement-fishers").exists()
        if has_attachments_clause or has_party_b_clause:
            if has_attachments_clause:
                attachments_clause = worker_contract_clauses.filter(kind="contract-clauses-attachments").first()
                attachments_content = json.loads(attachments_clause.content)
            if has_party_b_clause:
                party_b_clause = worker_contract_clauses.filter(
                    kind="contract-clauses-parties-requirement-fishers").first()
                party_b_content = json.loads(party_b_clause.content)
            # is_crew_account = attachments_content.get("isCrewMemberAccount")

            worker_initial_data["bank_account_name"] = attachments_content.get("accountName", None)
            worker_initial_data["bank_account_number"] = attachments_content.get("accountNumber", None)
            worker_initial_data["bank_name"] = attachments_content.get("bankName", None)
            worker_initial_data["cash_beneficiary_name"] = \
                party_b_content.get("familyMember", attachments_content.get("beneficiaryName", None))
            worker_initial_data["cash_beneficiary_contact"] = \
                party_b_content.get("familyMemberContactInfo", attachments_content.get("relativePhoneNumber", None))
            worker_initial_data["bank_transfer_beneficiary_name"] = \
                party_b_content.get("familyMember", attachments_content.get("beneficiaryName", None))
            worker_initial_data["bank_transfer_beneficiary_contact"] = \
                party_b_content.get("familyMemberContactInfo", attachments_content.get("relativePhoneNumber", None))

        # add worker_initial_data to initial_data
        initial_data.append(worker_initial_data)

    return initial_data


def generate_payment_field_labels(payments_common_text):
    return {
        "user": payments_common_text.get("crewName", "Crew name"),
        "payment_date": payments_common_text.get("paymentDate", "Payment date"),
        "payment_category": payments_common_text.get("paymentCategory", "Payment category"),
        "start_date": payments_common_text.get("startDate", "Start date"),
        "end_date": payments_common_text.get("endDate", "End date"),
        "total_usd_amount_received":
            f'{payments_common_text.get("totalAmount", "Total amount")} {payments_common_text.get("USD", "USD")}',
        "payment_method": payments_common_text.get("paymentMethod", "Payment method"),
        "cash_amount":
            f'{payments_common_text.get("cash", "CASH").upper()}: {payments_common_text.get("amount", "Amount")}',
        "cash_currency":
            f'{payments_common_text.get("cash", "CASH").upper()}: {payments_common_text.get("currency", "Currency")}',
        "cash_exchange_rate": f'{payments_common_text.get("cash", "CASH").upper()}: {payments_common_text.get("exchangeRate","Exchange rate")} (1 {payments_common_text.get("USD", "USD")} = ___)',
        "cash_beneficiary_relationship": f'{payments_common_text.get("cash", "CASH").upper()}: {payments_common_text.get("beneficiaryRelationship", "Beneficiary relationship")}',
        "cash_beneficiary_name": f'{payments_common_text.get("cash", "CASH").upper()}: {payments_common_text.get("beneficiaryName", "Beneficiary name")} ({payments_common_text.get("ifBeneficiaryIsNotCrewMember", "If beneficiary is not crew member")})',
        "cash_beneficiary_contact": f'{payments_common_text.get("cash", "CASH").upper()}: {payments_common_text.get("beneficiaryContact", "Beneficiary contact information")} ({payments_common_text.get("ifBeneficiaryIsNotCrewMember", "If beneficiary is not crew member")})',
        "bank_transfer_amount": f'{payments_common_text.get("bankTransfer", "BANK TRANSFER").upper()}: {payments_common_text.get("amount", "Amount")}',
        "bank_transfer_currency": f'{payments_common_text.get("bankTransfer", "BANK TRANSFER").upper()}: {payments_common_text.get("currency", "Currency")}',
        "bank_transfer_exchange_rate": f'{payments_common_text.get("bankTransfer", "BANK TRANSFER").upper()}: {payments_common_text.get("exchangeRate", "Exchange rate")} (1 {payments_common_text.get("USD", "USD")} = ___)',
        "bank_account_name": payments_common_text.get("bankAccountName", "Bank account name"),
        "bank_account_number": payments_common_text.get("bankAccountNumber", "Bank account number"),
        "bank_name": payments_common_text.get("bankName", "Bank name"),
        "bank_transfer_beneficiary_relationship": f'{payments_common_text.get("bankTransfer", "BANK TRANSFER").upper()}: {payments_common_text.get("beneficiaryRelationship", "Beneficiary relationship")}',
        "bank_transfer_beneficiary_name": f'{payments_common_text.get("bankTransfer", "BANK TRANSFER").upper()}: {payments_common_text.get("beneficiaryName", "Beneficiary name")} ({payments_common_text.get("ifBeneficiaryIsNotCrewMember", "If beneficiary is not crew member")})',
        "bank_transfer_beneficiary_contact": f'{payments_common_text.get("bankTransfer", "BANK TRANSFER").upper()}: {payments_common_text.get("beneficiaryContact", "Beneficiary contact information")} ({payments_common_text.get("ifBeneficiaryIsNotCrewMember", "If beneficiary is not crew member")})',
    }


def generate_payment_currency_options(payments_common_text):
    return [
        {"key": "USD", "label": payments_common_text.get("USDollar", "US dollar")},
        {"key": "MUR", "label": payments_common_text.get("MauritianRupee", "Mauritian Rupee")},
        {"key": "TWD", "label": payments_common_text.get("TaiwanNewDollars", "Taiwan New Dollars")},
        {"key": "IDR", "label": payments_common_text.get("IndonesianRupiah", "Indonesian Rupiah")},
        {"key": "SBD", "label": payments_common_text.get("SolomonIslandsDollar", "Solomon Islands Dollar")},
    ]


def generate_payment_beneficiary_options(payments_common_text):
    return [
        {"key": "self", "label": payments_common_text.get("crewMemberHimself", "Crew member himself")},
        {"key": "family_or_friend", "label": payments_common_text.get("familyOrFriend", "Family/friend")},
    ]


def generate_deductions_options(payments_common_text):
    return [
        {"key": "", "label": payments_common_text.get("pleaseSelectItem", "Please select item")},
        {"key": "deductions_allowed_under_employment_contract", "label":
         payments_common_text.get("deductions_allowed_under_employment_contract",
                                  "Deductions allowed under employment contract")},
        {"key": "cigarettes", "label": payments_common_text.get("cigarettes", "Cigarettes")},
        {"key": "toiletries", "label": payments_common_text.get("toiletries", "Toiletries")},
        {"key": "food_and_or_drinks", "label": payments_common_text.get("food_and_or_drinks", "Food and/or Drinks")},
        {"key": "medicine", "label": payments_common_text.get("medicine", "Medicine")},
        {"key": "wifi_or_phone_calls", "label": payments_common_text.get("wifi_or_phone_calls",
                                                                         "Wifi and/or Phone calls")},
        {"key": "loans_or_wage_advances", "label": payments_common_text.get("loans_or_wage_advances",
                                                                            "Loans and/or wage advances")},
        {"key": "other", "label": payments_common_text.get("other", "Other")},
    ]


def generate_payment_category_options(payments_common_text):
    return [
        {"key": "wages", "label": payments_common_text.get("wages", "Wages")},
        {"key": "bonus", "label": payments_common_text.get("bonus", "Bonus")},
    ]


def generate_payment_method_options(payments_common_text):
    return [
        {"key": "bank_transfer", "label": payments_common_text.get("bankTransfer", "Bank Transfer")},
        {"key": "cash", "label": payments_common_text.get("cash", "Cash")},
        {"key": "both", "label": payments_common_text.get("cash", "Both")},
    ]
