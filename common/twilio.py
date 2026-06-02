from twilio.rest import Client
from decouple import config
from django.contrib import messages


class OTPVerification:
    def __init__(self):
        self.account_sid = config('TWILIO_ACCOUNT_SID')
        self.auth_token = config('TWILIO_AUTH_TOKEN')
        self.verify_service_sid = config('TWILIO_VERIFY_SERVICE_SID')
        self.client = Client(self.account_sid, self.auth_token)

    def send_otp(self, phone_number, locale='en'):
        verification = self.client.verify.v2.services(self.verify_service_sid) \
            .verifications \
            .create(to=phone_number, channel="sms", locale=locale)
        return verification.status

    def check_otp(self, otp_code, phone_number):
        verification_check = self.client.verify.v2.services(self.verify_service_sid) \
            .verification_checks \
            .create(to=phone_number, code=otp_code)
        return verification_check.status

    def send_sms(self, phone_number, message):
        # TODO: set up a dedicated phone number for sending SMS and use it here
        message = self.client.messages.create(
            body=message,
            from_=config('TWILIO_PHONE_NUMBER'),
            to=phone_number
        )
        return message.sid


def send_verification_code(request, user, auth_common_text=None):
    try:
        otp_service = OTPVerification()
        locale = get_locale_from_request(request)
        otp_service.send_otp(user.mobile, locale=locale)
    except Exception:
        messages.error(request,
                       auth_common_text.get('errorSendingVerificationCode', 'Error sending verification code.'))


def check_verification_code(request, phone_number, otp_code, auth_common_text=None):
    try:
        otp_service = OTPVerification()
        verification_result = otp_service.check_otp(otp_code, phone_number)
        return verification_result == 'approved'
    except Exception:
        messages.error(request, auth_common_text.get('errorVerifyingCode', 'Error verifying code.'))
        return False


def get_locale_from_request(request):
    lang = request.session.get('language', 'en-us')
    if lang == 'en-us':
        return 'en'
    if lang == 'id-id':
        return 'ms'
    if lang == 'qm-zh':
        return 'zh'
    return 'en'
