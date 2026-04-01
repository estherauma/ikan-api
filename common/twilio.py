from twilio.rest import Client
from decouple import config


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
