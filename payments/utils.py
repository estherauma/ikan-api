from contracts.models import ContractClause
import json
from django.db.models import Q
from accounts.models import User


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
    "vessel_name",
    "crew_name",
    "payment_date",
    "payment_category",
    "payment_method",
    "beneficiary_name",
    "start_date",
    "end_date",
    "duration",
    "total_usd_amount_received",
]

required_cash_fields = [
    "cash_usd_amount",
    "cash_currency",
    "cash_local_amount",
    "cash_exchange_rate",
    "is_cash_beneficiary_crew",
    "cash_beneficiary_relationship",
    "cash_beneficiary_contact",
    "cash_beneficiary_contact_platform",
]

required_bank_transfer_fields = [
    "bank_transfer_usd_amount",
    "bank_transfer_currency",
    "bank_transfer_local_amount",
    "bank_transfer_exchange_rate",
    "is_bank_transfer_beneficiary_crew",
    "bank_account_name",
    "bank_account_number",
    "bank_name",
    "bank_transfer_beneficiary_relationship",
    "bank_transfer_beneficiary_contact",
    "bank_transfer_beneficiary_contact_platform",
]

categories_map = {"wages": "薪資 Wages", "bonus": "獎金 Bonus"}

payment_categories = [
    {"key": "wages", "value": "薪資 Wages"},
    {"key": "bonus", "value": "獎金 Bonus"},
]

payment_methods = [
    {"key": "bank_transfer", "value": "匯款 Bank Transfer"},
    {"key": "cash", "value": "現金 Cash"},
    {"key": "both", "value": "两个都 Both"},
]

payment_currencies = [
    {"key": "USD", "value": "US Dollar"},
    {"key": "TWD", "value": "新台幣 Taiwan New Dollars"},
    {"key": "MUR", "value": "毛里求斯盧比 Mauritian Rupee"},
    {"key": "IDR", "value": "印尼盾/盧比 Indonesian Rupiah"},
    {"key": "SBD", "value": "索羅門群島元 Solomon Islands Dollar"},
]

payment_fields = [
    "user",
    "payment_date",
    "payment_category",
    "beneficiary_name",
    "start_date",
    "end_date",
    "duration",
    "total_usd_amount_received",
    "payment_method",
    "cash_usd_amount",
    "cash_currency",
    "cash_local_amount",
    "cash_exchange_rate",
    "is_cash_beneficiary_crew",
    "cash_beneficiary_relationship",
    "cash_beneficiary_contact",
    "cash_beneficiary_contact_platform",
    "bank_transfer_usd_amount",
    "bank_transfer_currency",
    "bank_transfer_local_amount",
    "bank_transfer_exchange_rate",
    "is_bank_transfer_beneficiary_crew",
    "bank_account_name",
    "bank_account_number",
    "bank_name",
    "bank_transfer_beneficiary_relationship",
    "bank_transfer_beneficiary_contact",
    "bank_transfer_beneficiary_contact_platform",
    "has_deductions",
]

payment_fields_map_english = {
    "user": "Crew Name",
    "payment_date": "Payment Date",
    "payment_category": "Payment Category",
    "beneficiary_name": "Beneficiary Name",
    "start_date": "Payment for which month - start",
    "end_date": "Payment for which month - end",
    "duration": "Total No. of Months",
    "total_usd_amount_received": "Total Amount Received (USD)",
    "payment_method": "Payment Method",
    "cash_usd_amount": "Cash - Amount (USD) Note: If it's none, please insert zero",
    "cash_currency": "If the cash payment is made in：\
                            （1） non-USD currency, please select the currency used.\
                            (2) If cash payment is made in USD, please choose N/A.",
    "cash_local_amount": "If the cash payment is made in non-USD currency, \
        please state the cash amount paid in said currency.",
    "cash_exchange_rate": "Please state exchange rate in terms of how much is the cash payment currency to 1 USD",
    "is_cash_beneficiary_crew": "Is the cash beneficiary the crew member himself?",
    "cash_beneficiary_relationship": "Cash Beneficiary's Relationship with Crew",
    "cash_beneficiary_contact": "If cash beneficiary is not crew member him/herself,\
        please provide contact information relating to the account \
            (Telephone number、WhatsApp、Facebook、Others)",
    "cash_beneficiary_contact_platform": "Please choose which platform this cash \
        beneficiary contact information is for",
    "bank_transfer_usd_amount": "Bank transfer - Amount (USD) \
                            Note: If it's none, please insert zero",
    "bank_transfer_currency": "If the crew is accepting bank transfer payment in：\
                            （1) non-USD currency, please select the currency used.\
                            (2) If payment is made in USD, please choose N/A.",
    "bank_transfer_local_amount": "If the bank transfer payment is made in non-USD currency, \
        please state the amount paid in said currency.",
    "bank_transfer_exchange_rate": "Please state exchange rate in terms of how much is the \
        bank transfer payment currency to 1 USD",
    "is_bank_transfer_beneficiary_crew": "Is the bank transfer beneficiary the crew member himself?",
    "bank_account_name": "Beneficiary Account Name",
    "bank_account_number": "Beneficiary Account No.",
    "bank_name": "Beneficiary Bank Name\
                            *Type it in Bahasa / English",
    "bank_transfer_beneficiary_relationship": "Bank Transfer Beneficiary's Relationship with Crew",
    "bank_transfer_beneficiary_contact": "If bank transfer beneficiary is not crew member him/herself, \
        please provide contact information relating to the account（Telephone number、WhatsApp、Facebook, Others)",
    "bank_transfer_beneficiary_contact_platform": "Please choose which platform this bank transfer beneficiary \
        contact information is for",
    "has_deductions": "Are there any deductions?",
    "deduction_1": "deduction_1",
    "deduction_1_reason": "deduction_1_reason",
    "deduction_1_other_reason": "deduction_1_other_reason",
    "deduction_2": "deduction_2",
    "deduction_2_reason": "deduction_2_reason",
    "deduction_2_other_reason": "deduction_2_other_reason",
}

payment_fields_map_chinese = {
    "user": "船員名稱",
    "payment_date": "支付日期",
    "payment_category": "款項種類",
    "beneficiary_name": "授薪人名稱",
    "start_date": "支付的月份",
    "end_date": "支付的月份 - 終",
    "duration": "總月數",
    "total_usd_amount_received": "總額 （美金",
    "payment_method": "付款方式",
    "cash_usd_amount": "現金 - 總額 （美金） 注：如零請寫零",
    "cash_currency": "如支付的貨幣：\
                             (1) 非美金，請選擇支付的貨幣。\
                             (2) 是美金, 請選擇 ‘不適用’。",
    "cash_local_amount": "如支付的貨幣非美金，請列出支付貨幣的總額。",
    "cash_exchange_rate": "請說明支付貨幣兌換 1 美元的匯率",
    "is_cash_beneficiary_crew": "授款人是否船員本人？",
    "cash_beneficiary_relationship": "授薪人與船員關係",
    "cash_beneficiary_contact": "非船員本人,請提供帳戶聯絡資訊 (電話號碼、WhatsApp、Facebook、其他)",
    "cash_beneficiary_contact_platform": "請選擇聯絡資訊的平台",
    "bank_transfer_usd_amount": "匯款 - 總額 （美金） 注：如零請寫零",
    "bank_transfer_currency": "如船員收到的貨幣：\
                             (1) 非美金，請選擇有關貨幣。\
                             (2) 是美金，請選擇 ‘不適用’。",
    "bank_transfer_local_amount": "如支付的貨幣非美金，請列出支付貨幣的總額。",
    "bank_transfer_exchange_rate": "請說明支付貨幣兌換 1 美元的匯率",
    "is_bank_transfer_beneficiary_crew": "授款人是否船員本人?",
    "bank_account_name": "銀行戶名",
    "bank_account_number": "銀行帳號",
    "bank_name": "銀行名稱 *Type it in Bahasa / English",
    "bank_transfer_beneficiary_relationship": "授薪人與船員關係",
    "bank_transfer_beneficiary_contact": "非船員本人, 請提供帳戶聯絡資訊 (電話號碼、WhatsApp、Facebook、其他)",
    "bank_transfer_beneficiary_contact_platform": "請選擇聯絡資訊的平台",
    "has_deductions": "是否有扣除?",
    "deduction_1": "扣除一 Deduction 1",
    "deduction_1_reason": "扣除原因 Reason for deduction 1",
    "deduction_1_other_reason": '如扣除原因是“其他”，請列明原因 If the reason for deduction 1 is "Others", please state the reason',
    "deduction_2": "扣除2 Deduction 2",
    "deduction_2_reason": "扣除原因 Reason for deduction 2",
    "deduction_2_other_reason": '如扣除原因是“其他”，請列明原因 If the reason for deduction 2 is "Others", please state the reason',
}

deduction_fields = [
    "deduction_1",
    "deduction_1_reason",
    "deduction_1_other_reason",
    "deduction_2",
    "deduction_2_reason",
    "deduction_2_other_reason",
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
