display_col_name_to_key_map = {
    "船舶名稱\nVessel Name\n": "vessel_name",
    "船員名稱 \nCrew Name\n\n": "crew_name",
    "支付日期 \nPayment Date\n\n": "payment_date",
    "款項種類\nPayment Category\n\n": "payment_category",
    "授薪人名稱\nBeneficiary Name\n\n": "beneficiary_name",
    "支付的月份 - 始\nPayment for which month - start\n\n": "start_date",
    "支付的月份 - 終\nPayment for which month - end\n": "end_date",
    "總月數\nTotal No. of Months": "duration",
    "總額 （美金）\nTotal Amount Received (USD)": "total_usd_amount_received",
    "現金 - 總額 （美金）\n注：如零請寫零\n\nCash - Amount (USD)\nNote: If it's none, please insert zero": "cash_usd_amount",
    "如支付的貨幣：\n（1） 非美金，請選擇支付的貨幣。\n（2）是美金，請選擇 ‘不適用’。\n\nIf the cash payment is made in：\n（1） non-USD currency, please select the currency used.\n(2) If cash payment is made in USD, please choose N/A.": "cash_currency",
    "如支付的貨幣非美金，請列出支付貨幣的總額。\n\nIf the cash payment is made in non-USD currency, please state the cash amount paid in said currency.": "cash_local_amount",
    "請說明支付貨幣兌換 1 美元的匯率\nPlease state exchange rate in terms of how much is the cash payment currency to 1 USD ": "cash_exchange_rate",
    "授款人是否船員本人？Is the cash beneficiary the crew member himself?": "is_cash_beneficiary_crew",
    "授薪人與船員關係\nCash Beneficiary's Relationship with Crew": "cash_beneficiary_relationship",
    "非船員本人,請提供帳戶聯絡\n資訊\nIf cash beneficiary is not crew member him/herself, please provide contact information relating to the account\n\n（電話號碼 Telephone number、WhatsApp、FB、其他Others)": "cash_beneficiary_contact",
    "請選擇聯絡資訊的平台\n\nPlease choose which platform this cash beneficiary contact information is for": "cash_beneficiary_contact_platform",
    "匯款 - 總額 （美金）\n注：如零請寫零\n\nBank transfer - Amount (USD)\nNote: If it's none, please insert zero": "bank_transfer_usd_amount",
    "如船員收到的貨幣：\n（1） 非美金，請選擇有關貨幣。\n（2）是美金，請選擇 ‘不適用’。\n\nIf the crew is accepting bank transfer payment in：\n（1) non-USD currency, please select the currency used.\n(2) If payment is made in USD, please choose N/A.": "bank_transfer_currency",
    "如支付的貨幣非美金，請列出支付貨幣的總額。\n\nIf the bank transfer payment is made in non-USD currency, please state the amount paid in said currency.": "bank_transfer_local_amount",
    "請說明支付貨幣兌換 1 美元的匯率\n\nPlease state exchange rate in terms of how much is the bank transfer payment currency to 1 USD ": "bank_transfer_exchange_rate",
    "授款人是否船員本人？Is the bank transfer beneficiary the crew member himself?": "is_bank_transfer_beneficiary_crew",
    "銀行戶名\nBeneficiary Account Name": "bank_account_name",
    "銀行帳號 \nBeneficiary Account No.": "bank_account_number",
    "銀行名稱\nBeneficiary Bank Name\n\n*Type it in Bahasa / English": "bank_name",
    "授薪人與船員關係\nBank Transfer Beneficiary's Relationship with Crew": "bank_transfer_beneficiary_relationship",
    "非船員本人, 請提供帳戶聯絡\n資訊\nIf bank transfer beneficiary is not crew member him/herself, please provide contact information relating to the account\n\n（電話號碼 Telephone number、WhatsApp、FB、其他Others)": "bank_transfer_beneficiary_contact",
    "請選擇聯絡資訊的平台\n\nPlease choose which platform this bank transfer beneficiary contact information is for": "bank_transfer_beneficiary_contact_platform",
    "是否有扣除？\nAre there any deductions?": "has_deductions",
    "扣除一 （美金）\nDeduction 1 (USD)": "deduction_1",
    "扣除原因\nReason for deduction 1": "deduction_1_reason",
    '如扣除原因是“其他”，請列明原因\n\nIf the reason for deduction 1 is "Others", please state the reason': "deduction_1_other_reason",
    "扣除2 （美金）\nDeduction 2 (USD)": "deduction_2",
    "扣除原因\nReason for deduction 2": "deduction_2_reason",
    '如扣除原因是“其他”，請列明原因\n\nIf the reason for deduction 2 is "Others", please state the reason': "deduction_2_other_reason",
    "付款方式\nPayment Method": "payment_method",
}

currencies_map = {
    "Taiwan new dollar": "TWD",
    "US Dollar": "USD",
    "Indonesian rupiah": "IDR",
    "Mauritian rupee": "MUR",
    "Solomon Islands dollar": "SBD",
    "毛里求斯盧比 Mauritian Rupee": "MUR",
    "新台幣 Taiwan New Dollars": "TWD",
    "印尼盾/盧比 Indonesian Rupiah": "IDR",
    "索羅門群島元 Solomon Islands Dollar": "SBD",
    "不適用 N/A": "USD",  # default to USD
}

boolean_values_map = {
    "Yes": True,
    "No": False,
    "是 Yes": True,
    "否 No": False,
}

methods_map = {
    "現金 Cash": "cash",
    "匯款 Bank Transfer": "bank_transfer",
    "Cash": "cash",
    "Bank Transfer": "bank_transfer",
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

categories_map = {"薪資 Wages": "Wages", "獎金 Bonus": "Bonus"}

payment_categories = [
    {"key": "wages", "value": "薪資 Wages"},
    {"key": "bonus", "value": "獎金 Bonus"},
]

payment_methods = [
    {"key": "bank_transfer", "value": "匯款 Bank Transfer"},
    {"key": "cash", "value": "現金 Cash"},
    {"key": "both", "value": "Both"},
]

payment_currencies = [
    {"key": "USD", "value": "US Dollar"},
    {"key": "TWD", "value": "新台幣 Taiwan New Dollars"},
    {"key": "MUR", "value": "毛里求斯盧比 Mauritian Rupee"},
    {"key": "IDR", "value": "印尼盾/盧比 Indonesian Rupiah"},
    {"key": "SBD", "value": "索羅門群島元 Solomon Islands Dollar"},
]
