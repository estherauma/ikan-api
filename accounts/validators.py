from django.contrib.auth.password_validation import (
    UserAttributeSimilarityValidator,
    MinimumLengthValidator,
    CommonPasswordValidator,
    NumericPasswordValidator,
)
from django.core.exceptions import ValidationError
from accounts.middleware import get_current_request
from content.utils import ContentUtils


def get_auth_common_text():
    request = get_current_request()
    if request is None:
        return {}

    try:
        return ContentUtils(request).get_page_text('auth-common-text') or {}
    except Exception:
        return {}


class CustomUserAttributeSimilarityValidator(UserAttributeSimilarityValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            auth_common_text = get_auth_common_text()
            raise ValidationError(
                auth_common_text.get(
                    'passwordTooSimilarToPersonalInfo',
                    'The password is too similar to your personal information.'
                ),
                code="password_too_similar",
            )


class CustomMinimumLengthValidator(MinimumLengthValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            auth_common_text = get_auth_common_text()
            raise ValidationError(
                auth_common_text.get(
                    'passwordTooShort',
                    'This password is too short. It must contain at least %(min_length)d characters.'
                ),
                code="password_too_short",
                params={"min_length": self.min_length},
            )


class CustomCommonPasswordValidator(CommonPasswordValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            auth_common_text = get_auth_common_text()
            raise ValidationError(
                auth_common_text.get(
                    'passwordTooCommon',
                    'This password is too common.'
                ),
                code="password_too_common",
            )


class CustomNumericPasswordValidator(NumericPasswordValidator):
    def validate(self, password, user=None):
        try:
            super().validate(password, user)
        except ValidationError:
            auth_common_text = get_auth_common_text()
            raise ValidationError(
                auth_common_text.get(
                    'passwordEntirelyNumeric',
                    'This password is entirely numeric.'
                ),
                code="password_entirely_numeric",
            )
