from typing import Optional

import graphene
import jwt
from django.core.exceptions import ValidationError
from django.middleware.csrf import _compare_masked_tokens  # type: ignore
from django.middleware.csrf import _get_new_csrf_token
from django.utils import timezone
from django.utils.crypto import get_random_string
from graphene.types.generic import GenericScalar

from ....account import models
from ....account.error_codes import AccountErrorCode
from ....core.jwt import (
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    JWT_REFRESH_TYPE,
    PERMISSIONS_FIELD,
    create_access_token,
    create_refresh_token,
    get_user_from_payload,
    jwt_decode,
)
from ....core.permissions import get_permissions_from_names
from ...core.mutations import BaseMutation
from ...core.types.common import AccountError
from ..types import User


def get_payload(token):
    try:
        payload = jwt_decode(token)
    except jwt.ExpiredSignatureError:
        raise ValidationError(
            "Signature has expired", code=AccountErrorCode.JWT_SIGNATURE_EXPIRED.value
        )
    except jwt.DecodeError:
        raise ValidationError(
            "Error decoding signature", code=AccountErrorCode.JWT_DECODE_ERROR.value
        )
    except jwt.InvalidTokenError:
        raise ValidationError(
            "Invalid token", code=AccountErrorCode.JWT_INVALID_TOKEN.value
        )
    return payload


def get_user(payload):
    try:
        user = get_user_from_payload(payload)
    except Exception:
        user = None
    if not user:
        raise ValidationError(
            "Invalid token", code=AccountErrorCode.JWT_INVALID_TOKEN.value
        )
    permissions = payload.get(PERMISSIONS_FIELD)
    if permissions is not None:
        user.effective_permissions = get_permissions_from_names(permissions)
    return user


class CreateToken(BaseMutation):
    """Mutation that authenticates a user and returns token and user data."""

    class Arguments:
        email = graphene.String(required=True, description="Email of a user.")
        password = graphene.String(required=True, description="Password of a user.")

    class Meta:
        description = "Create JWT token."
        error_type_class = AccountError
        error_type_field = "account_errors"

    token = graphene.String(description="JWT token, required to authenticate.")
    refresh_token = graphene.String(
        description="JWT refresh token, required to re-generate access token."
    )
    csrf_token = graphene.String(
        description="CSRF token required to re-generate access token."
    )
    user = graphene.Field(User, description="A user instance.")

    @classmethod
    def _retrieve_user_from_credentials(cls, email, password) -> Optional[models.User]:
        user = models.User.objects.filter(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    @classmethod
    def get_user(cls, _info, data):
        user = cls._retrieve_user_from_credentials(data["email"], data["password"])
        if not user:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Please, enter valid credentials",
                        code=AccountErrorCode.INVALID_CREDENTIALS.value,
                    )
                }
            )
        if not user.is_active and not user.last_login:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Account needs to be confirmed via email.",
                        code=AccountErrorCode.ACCOUNT_NOT_CONFIRMED.value,
                    )
                }
            )

        if not user.is_active and user.last_login:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Account inactive.",
                        code=AccountErrorCode.INACTIVE.value,
                    )
                }
            )
        return user

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = cls.get_user(info, data)
        access_token = create_access_token(user)
        csrf_token = _get_new_csrf_token()
        refresh_token = create_refresh_token(user, {"csrfToken": csrf_token})
        info.context.refresh_token = refresh_token
        info.context._cached_user = user
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return cls(
            errors=[],
            user=user,
            token=access_token,
            refresh_token=refresh_token,
            csrf_token=csrf_token,
        )


class RefreshToken(BaseMutation):
    """Mutation that refresh user token and returns token and user data."""

    token = graphene.String(description="JWT token, required to authenticate.")
    user = graphene.Field(User, description="A user instance.")

    class Arguments:
        refresh_token = graphene.String(required=False, description="Refresh token.")
        csrf_token = graphene.String(
            required=False,
            description=(
                "CSRF token required to refresh token. This argument is "
                "required when refreshToken is provided as a cookie."
            ),
        )

    class Meta:
        description = (
            "Refresh JWT token. Mutation tries to take refreshToken from the input."
            "If it fails it will try to take refreshToken from the http-only cookie -"
            f"{JWT_REFRESH_TOKEN_COOKIE_NAME}. csrfToken is required when refreshToken "
            "is provided as a cookie."
        )
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def get_refresh_token_payload(cls, refresh_token):
        try:
            payload = get_payload(refresh_token)
        except ValidationError as e:
            raise ValidationError({"refreshToken": e})
        return payload

    @classmethod
    def get_refresh_token(cls, info, data):
        request = info.context
        refresh_token = request.COOKIES.get(JWT_REFRESH_TOKEN_COOKIE_NAME, None)
        refresh_token = data.get("refresh_token") or refresh_token
        return refresh_token

    @classmethod
    def clean_refresh_token(cls, refresh_token):
        if not refresh_token:
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Missing refreshToken",
                        code=AccountErrorCode.JWT_MISSING_TOKEN.value,
                    )
                }
            )
        payload = cls.get_refresh_token_payload(refresh_token)
        if payload["type"] != JWT_REFRESH_TYPE:
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Incorrect refreshToken",
                        code=AccountErrorCode.JWT_INVALID_TOKEN.value,
                    )
                }
            )
        return payload

    @classmethod
    def clean_csrf_token(cls, csrf_token, payload):
        if not csrf_token:
            msg = "CSRF token is required when refreshToken is provided by the cookie"
            raise ValidationError(
                {
                    "csrf_token": ValidationError(
                        msg,
                        code=AccountErrorCode.REQUIRED.value,
                    )
                }
            )
        is_valid = _compare_masked_tokens(csrf_token, payload["csrfToken"])
        if not is_valid:
            raise ValidationError(
                {
                    "csrf_token": ValidationError(
                        "Invalid csrf token",
                        code=AccountErrorCode.JWT_INVALID_CSRF_TOKEN.value,
                    )
                }
            )

    @classmethod
    def get_user(cls, payload):
        try:
            user = get_user(payload)
        except ValidationError as e:
            raise ValidationError({"refresh_token": e})
        return user

    @classmethod
    def perform_mutation(cls, root, info, **data):
        refresh_token = cls.get_refresh_token(info, data)
        payload = cls.clean_refresh_token(refresh_token)

        # None when we got refresh_token from cookie.
        if not data.get("refresh_token"):
            csrf_token = data.get("csrf_token")
            cls.clean_csrf_token(csrf_token, payload)

        user = get_user(payload)
        token = create_access_token(user)
        return cls(errors=[], user=user, token=token)


class VerifyToken(BaseMutation):
    """Mutation that confirms if token is valid and also returns user data."""

    user = graphene.Field(User, description="User assigned to token.")
    is_valid = graphene.Boolean(
        required=True,
        default_value=False,
        description="Determine if token is valid or not.",
    )
    payload = GenericScalar(description="JWT payload.")

    class Arguments:
        token = graphene.String(required=True, description="JWT token to validate.")

    class Meta:
        description = "Verify JWT token."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def get_payload(cls, token):
        try:
            payload = get_payload(token)
        except ValidationError as e:
            raise ValidationError({"token": e})
        return payload

    @classmethod
    def get_user(cls, payload):
        try:
            user = get_user(payload)
        except ValidationError as e:
            raise ValidationError({"token": e})
        return user

    @classmethod
    def perform_mutation(cls, root, info, **data):
        token = data["token"]
        payload = cls.get_payload(token)
        user = cls.get_user(payload)
        return cls(errors=[], user=user, is_valid=True, payload=payload)


class DeactivateAllUserTokens(BaseMutation):
    class Meta:
        description = "Deactivate all JWT tokens of the currently authenticated user."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        user.jwt_token_key = get_random_string()
        user.save(update_fields=["jwt_token_key"])
        return cls()


class ExternalAuthenticationUrl(BaseMutation):
    """Prepare external authentication url for user by a custom plugin."""

    authentication_data = graphene.JSONString(
        description="The data returned by authentication plugin."
    )

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = graphene.JSONString(
            required=True,
            description=(
                "The data required by plugin to create external authentication url."
            ),
        )

    class Meta:
        description = "Prepare external authentication url for user by custom plugin."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        request = info.context
        plugin_id = data["plugin_id"]
        input_data = data["input"]
        manager = info.context.plugins
        return cls(
            authentication_data=manager.external_authentication_url(
                plugin_id, input_data, request
            )
        )


class ExternalObtainAccessTokens(BaseMutation):
    """Obtain external access tokens by a custom plugin."""

    token = graphene.String(description="The token, required to authenticate.")
    refresh_token = graphene.String(
        description="The refresh token, required to re-generate external access token."
    )
    csrf_token = graphene.String(
        description="CSRF token required to re-generate external access token."
    )
    user = graphene.Field(User, description="A user instance.")

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = graphene.JSONString(
            required=True,
            description="The data required by plugin to create authentication data.",
        )

    class Meta:
        description = "Obtain external access tokens for user by custom plugin."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        request = info.context
        plugin_id = data["plugin_id"]
        input_data = data["input"]
        manager = info.context.plugins
        access_tokens_response = manager.external_obtain_access_tokens(
            plugin_id, input_data, request
        )
        info.context.refresh_token = access_tokens_response.refresh_token

        if access_tokens_response.user and access_tokens_response.user.id:
            info.context._cached_user = access_tokens_response.user
            access_tokens_response.user.last_login = timezone.now()
            access_tokens_response.user.save(update_fields=["last_login"])

        return cls(
            token=access_tokens_response.token,
            refresh_token=access_tokens_response.refresh_token,
            csrf_token=access_tokens_response.csrf_token,
            user=access_tokens_response.user,
        )


class ExternalRefresh(BaseMutation):
    """Refresh user's access by a custom plugin."""

    token = graphene.String(description="The token, required to authenticate.")
    refresh_token = graphene.String(
        description="The refresh token, required to re-generate external access token."
    )
    csrf_token = graphene.String(
        description="CSRF token required to re-generate external access token."
    )
    user = graphene.Field(User, description="A user instance.")

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = graphene.JSONString(
            required=True,
            description="The data required by plugin to proceed the refresh process.",
        )

    class Meta:
        description = "Refresh user's access by custom plugin."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        request = info.context
        plugin_id = data["plugin_id"]
        input_data = data["input"]
        manager = info.context.plugins
        access_tokens_response = manager.external_refresh(
            plugin_id, input_data, request
        )
        info.context.refresh_token = access_tokens_response.refresh_token
        if access_tokens_response.user and access_tokens_response.user.id:
            info.context._cached_user = access_tokens_response.user

        return cls(
            token=access_tokens_response.token,
            refresh_token=access_tokens_response.refresh_token,
            csrf_token=access_tokens_response.csrf_token,
            user=access_tokens_response.user,
        )


class ExternalLogout(BaseMutation):
    """Logout user by a custom plugin."""

    logout_data = graphene.JSONString(
        description="The data returned by authentication plugin."
    )

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = graphene.JSONString(
            required=True,
            description="The data required by plugin to proceed the logout process.",
        )

    class Meta:
        description = "Logout user by custom plugin."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        request = info.context
        plugin_id = data["plugin_id"]
        input_data = data["input"]
        manager = info.context.plugins
        return cls(logout_data=manager.external_logout(plugin_id, input_data, request))


class ExternalVerify(BaseMutation):
    user = graphene.Field(User, description="User assigned to data.")
    is_valid = graphene.Boolean(
        required=True,
        default_value=False,
        description="Determine if authentication data is valid or not.",
    )
    verify_data = graphene.JSONString(description="External data.")

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = graphene.JSONString(
            required=True,
            description="The data required by plugin to proceed the verification.",
        )

    class Meta:
        description = "Verify external authentication data by plugin."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(cls, root, info, **data):
        request = info.context
        plugin_id = data["plugin_id"]
        input_data = data["input"]
        manager = info.context.plugins
        user, data = manager.external_verify(plugin_id, input_data, request)
        return cls(user=user, is_valid=bool(user), verify_data=data)
