from contracts.models import ContractClause
import json
from django.db.models import Q
from accounts.models import User
from django.utils.timezone import now


currencies_map = {
    "USD": "美元 US dollar",
    "MUR": "毛里求斯盧比 Mauritian Rupee",
    "TWD": "新台幣 Taiwan New Dollars",
    "IDR": "印尼盾/盧比 Indonesian Rupiah",
    "SBD": "索羅門群島元 Solomon Islands Dollar",
}

boolean_values_map = {
    "Yes": True,
    "No": False,
    "是 Yes": True,
    "否 No": False,
}

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

categories_map = {"wages": "薪資 Wages", "bonus": "獎金 Bonus"}

beneficiaries_map = {
    "self": "船員自己 Crew member himself",
    "family_or_friend": "家人/朋友 Family/friend",
}

payment_categories = [
    {"key": "wages", "label": "薪資 Wages"},
    {"key": "bonus", "label": "獎金 Bonus"},
]

payment_methods = [
    {"key": "bank_transfer", "label": "匯款 Bank Transfer"},
    {"key": "cash", "label": "現金 Cash"},
    {"key": "both", "label": "現金和匯款 Cash and Bank transfer"},
]

payment_currencies = [
    {"key": "USD", "label": "US Dollar"},
    {"key": "TWD", "label": "新台幣 Taiwan New Dollars"},
    {"key": "MUR", "label": "毛里求斯盧比 Mauritian Rupee"},
    {"key": "IDR", "label": "印尼盾/盧比 Indonesian Rupiah"},
    {"key": "SBD", "label": "索羅門群島元 Solomon Islands Dollar"},
]

payment_beneficiarires = [
    {"key": "self", "label": "船員自己 Crew member himself"},
    {"key": "family_or_friend", "label": "家人/朋友 Family/friend"},
]

deductions_list = [
    {"key": "", "label": "請選擇項目 Please select item"},
    {"key": "deductions_allowed_under_employment_contract", "label": "契約允許的扣除項目 Deductions allowed under employment contract"},
    {"key": "cigarettes", "label": "香菸 Cigarettes"},
    {"key": "toiletries", "label": "浴室用品 Toiletries"},
    {"key": "food_and_or_drinks", "label": "食物和/或飲料 Food and/or Drinks"},
    {"key": "medicine", "label": "藥物 Medicine"},
    {"key": "wifi_or_phone_calls", "label": "無線上網和/或電話費用 Wifi and/or Phone calls"},
    {"key": "loans_or_wage_advances", "label": "借貸和/或預支薪資 Loans and/or wage advances"},
    {"key": "other", "label": "其他 Other"},
]

deductions_list_chinese = [
    {"key": "", "label": "請選擇項目"},
    {"key": "deductions_allowed_under_employment_contract", "label": "契約允許的扣除項目"},
    {"key": "cigarettes", "label": "香菸"},
    {"key": "toiletries", "label": "浴室用品"},
    {"key": "food_and_or_drinks", "label": "食物和/或飲料"},
    {"key": "medicine", "label": "藥物"},
    {"key": "wifi_or_phone_calls", "label": "無線上網和/或電話費用"},
    {"key": "loans_or_wage_advances", "label": "借貸和/或預支薪資"},
    {"key": "other", "label": "其他"},
]

deductions_list_bahasa = [
    {"key": "", "label": ""},
    {"key": "deductions_allowed_under_employment_contract", "label": "Potongan yang diizinkan dalam kontrak kerja"},
    {"key": "cigarettes", "label": "Rokok"},
    {"key": "toiletries", "label": "Peralatan mandi"},
    {"key": "food_and_or_drinks", "label": "Makanan dan Minuman"},
    {"key": "medicine", "label": "Obat-obatan"},
    {"key": "wifi_or_phone_calls", "label": "Wifi dan Telepon"},
    {"key": "loans_or_wage_advances", "label": "Pinjaman dan uang muka gaji"},
    {"key": "other", "label": "lain-lain"},
]

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

# english fields translations
payment_fields_map_english = {
    "user": "Crew Name",
    "payment_date": "Payment Date",
    "payment_category": "Payment Category",
    "start_date": "Wage month - start",
    "end_date": "Wage month - end",
    "total_usd_amount_received": "Total Amount (USD)",
    "payment_method": "Payment Method",
    "cash_amount": "CASH: Amount",
    "cash_currency": "CASH: Currency",
    "cash_exchange_rate": "CASH: Exchange rate used (1 USD = ___)",
    "cash_beneficiary_relationship": "CASH: Beneficiary",
    "cash_beneficiary_name": "CASH: Beneficiary's name (If beneficiary is not crew member)",
    "cash_beneficiary_contact": "CASH: Beneficiary's contact information (If beneficiary is not crew member)",
    "bank_transfer_amount": "BANK TRANSFER: Amount",
    "bank_transfer_currency": "BANK TRANSFER: Currency",
    "bank_transfer_exchange_rate": "BANK TRANSFER: Exchange rate used (1 USD = ___)",
    "bank_account_name": "BANK TRANSFER: Bank Account Name",
    "bank_account_number": "BANK TRANSFER: Bank Account Number",
    "bank_name": "BANK TRANSFER: Bank Name",
    "bank_transfer_beneficiary_relationship": "BANK TRANSFER: Beneficiary",
    "bank_transfer_beneficiary_name": "BANK TRANSFER: Beneficiary's name (If beneficiary is not crew member)",
    "bank_transfer_beneficiary_contact": "BANK TRANSFER: Beneficiary's contact information \
        (If beneficiary is not crew member)",
    # other fields
    "has_deductions": "Are there any deductions?",
    "deduction_1": "deduction_1",
    "deduction_1_reason": "deduction_1_reason",
    "deduction_1_other_reason": "deduction_1_other_reason",
    "deduction_2": "deduction_2",
    "deduction_2_reason": "deduction_2_reason",
    "deduction_2_other_reason": "deduction_2_other_reason",
    "add_deduction": "Add Deduction",
    "view_deductions": "View Deductions",
    "deductions": "Deductions",
}

# chinese fields translations
payment_fields_map_chinese = {
    "user": "船員名稱",
    "payment_date": "支付日期",
    "payment_category": "薪資或獎金",
    "start_date": "薪資月份 - 日期開始",
    "end_date": "薪資月份 - 日期終",
    "total_usd_amount_received": "總額 （美金)",
    "payment_method": "給付方式",
    "cash_amount": "現金：總額",
    "cash_currency": "現金：幣別",
    "cash_exchange_rate": "現金：匯率 (1美金 = ____)",
    "cash_beneficiary_relationship": "現金：受益人",
    "cash_beneficiary_name": "現金：受益人名稱 (如受益人非船員)",
    "cash_beneficiary_contact": "現金: 受益人聯絡方式 (如受益人非船員)",
    "bank_transfer_amount": "匯款: 總額",
    "bank_transfer_currency": "匯款: 幣別",
    "bank_transfer_exchange_rate": "匯款：匯率 (1美金 = ____)",
    "bank_account_name": "匯款：銀行帳號",
    "bank_account_number": "匯款: 銀行帳號",
    "bank_name": "匯款: 銀行名稱",
    "bank_transfer_beneficiary_relationship": "匯款：受益人",
    "bank_transfer_beneficiary_name": "匯款: 受益人名稱 (如受益人非船員)",
    "bank_transfer_beneficiary_contact": "匯款: 受益人聯絡方式 (如受益人非船員)",
    # other fields
    "has_deductions": "是否有扣除?",
    "deduction_1": "扣除一 Deduction 1",
    "deduction_1_reason": "扣除原因 Reason for deduction 1",
    "deduction_1_other_reason": '如扣除原因是“其他”，請列明原因 If the reason for deduction 1 is "Others", please state the reason',
    "deduction_2": "扣除2 Deduction 2",
    "deduction_2_reason": "扣除原因 Reason for deduction 2",
    "deduction_2_other_reason": '如扣除原因是“其他”，請列明原因 If the reason for deduction 2 is "Others", please state the reason',
    "add_deduction": "新增扣除",
    "view_deductions": "查看扣除",
    "deductions": "扣除",
}


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

        # add worker_initial_data to initial_data
        initial_data.append(worker_initial_data)

    return initial_data
