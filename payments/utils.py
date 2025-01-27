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
