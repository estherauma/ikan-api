from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from decouple import config
from django.contrib import messages


class OTPVerification:
    def __init__(self):
        self.account_sid = config('TWILIO_ACCOUNT_SID')
        self.auth_token = config('TWILIO_AUTH_TOKEN')
        self.verify_service_sid = config('TWILIO_VERIFY_SERVICE_SID')
        self.client = Client(self.account_sid, self.auth_token)

    def send_otp(self, phone_number, locale='en'):
        try:
            verification = self.client.verify.v2.services(self.verify_service_sid) \
                .verifications \
                .create(to=phone_number, channel="sms", locale=locale)
            if verification.status == "pending":
                return {
                    "success": True,
                    "status": "pending",
                    "message": "OTP sent successfully."
                }
            else:
                return {
                    "success": False,
                    "status": "failed",
                    "message": "Failed to send OTP.",
                    "errorKey": "otpCodeGenerationFailed"
                }
        except TwilioRestException as e:
            if e.code == 60200 or e.code == 60006 or e.status == 400:
                return {
                    "success": False,
                    "status": "invalid_number",
                    "message": "The provided phone number is invalid.",
                    "errorKey": "otpCodeGenerationInvalidNumber"
                }
            elif e.code == 19034:
                return {
                    "success": False,
                    "status": "invalid_country_code",
                    "message": "The provided phone number has an invalid country code.",
                    "errorKey": "otpCodeGenerationInvalidCountryCode"
                }
            elif e.status == 429 or e.code == 60203 or e.code == 60202 or e.code == 60211 or e.code == 60212:
                return {
                    "success": False,
                    "status": "too_many_requests",
                    "message": "Too many requests have been made to this number. Please try again later.",
                    "errorKey": "otpCodeGenerationTooManyRequests"
                }
            elif e.code == 60205:
                return {
                    "success": False,
                    "status": "sms_not_supported",
                    "message": "The provided phone number does not support receiving SMS messages.",
                    "errorKey": "otpCodeGenerationSMSNotSupported"
                }
            elif e.code == 60410 or e.code == 60412 or e.status == 403:
                return {
                    "success": False,
                    "status": "blocked",
                    "message": "This number has been temporarily blocked due to too many attempts.",
                    "errorKey": "otpCodeGenerationBlocked"
                }
            else:
                return {
                    "success": False,
                    "status": "twilio_api_error",
                    "message": f"Twilio API Error ({e.code}): {e.msg}",
                    "errorKey": "otpCodeGenerationTwilioAPIError"
                }
        except Exception as e:
            return {
                "success": False,
                "status": "server_error",
                "message": f"An unexpected system error occurred: {str(e)}",
                "errorKey": "otpCodeGenerationServerError"
            }

    def check_otp(self, otp_code, phone_number):
        try:
            verification_check = self.client.verify.v2.services(self.verify_service_sid) \
                .verification_checks \
                .create(to=phone_number, code=otp_code)
            if verification_check.status == "approved":
                return {
                    "success": True,
                    "status": "approved",
                    "message": "Verification successful."
                }
            else:
                return {
                    "success": False,
                    "status": "pending",
                    "message": "Invalid OTP code provided."
                }
        except TwilioRestException as e:
            if e.status == 404:
                return {
                    "success": False,
                    "status": "expired_or_max_attempts",
                    "message": "The verification session has expired, was already approved, \
                        or max retry attempts were reached.",
                }
            elif e.status == 429 or e.code == 60202:
                return {
                    "success": False,
                    "status": "blocked",
                    "message": "This number has been temporarily blocked due to too many attempts."
                }
            else:
                return {
                    "success": False,
                    "status": "twilio_api_error",
                    "message": f"Twilio API Error ({e.code}): {e.msg}"
                }
        except Exception as e:
            return {
                "success": False,
                "status": "server_error",
                "message": f"An unexpected system error occurred: {str(e)}"
            }

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
        return verification_result.get('status') == 'approved'
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
