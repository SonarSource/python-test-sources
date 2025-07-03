import graphene
import jwt
from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from ....account import events as account_events
from ....account import models, notifications, search, utils
from ....account.error_codes import AccountErrorCode
from ....checkout import AddressType
from ....core.jwt import create_token, jwt_decode
from ....core.tokens import account_delete_token_generator
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....giftcard.utils import assign_user_gift_cards
from ....order.utils import match_orders_with_new_user
from ....settings import JWT_TTL_REQUEST_EMAIL_CHANGE
from ...channel.utils import clean_channel
from ...core.enums import LanguageCodeEnum
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.types.common import AccountError
from ...meta.mutations import MetadataInput
from ..enums import AddressTypeEnum
from ..i18n import I18nMixin
from ..types import Address, AddressInput, User
from .base import (
    INVALID_TOKEN,
    BaseAddressDelete,
    BaseAddressUpdate,
    BaseCustomerCreate,
)


class AccountBaseInput(graphene.InputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    language_code = graphene.Argument(
        LanguageCodeEnum, required=False, description="User language code."
    )


class AccountRegisterInput(AccountBaseInput):
    email = graphene.String(description="The email address of the user.", required=True)
    password = graphene.String(description="Password.", required=True)
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    redirect_url = graphene.String(
        description=(
            "Base of frontend URL that will be needed to create confirmation URL."
        ),
        required=False,
    )
    language_code = graphene.Argument(
        LanguageCodeEnum, required=False, description="User language code."
    )
    metadata = graphene.List(
        graphene.NonNull(MetadataInput),
        description="User public metadata.",
        required=False,
    )
    channel = graphene.String(
        description=(
            "Slug of a channel which will be used to notify users. Optional when "
            "only one channel exists."
        )
    )


class AccountRegister(ModelMutation):
    class Arguments:
        input = AccountRegisterInput(
            description="Fields required to create a user.", required=True
        )

    requires_confirmation = graphene.Boolean(
        description="Informs whether users need to confirm their email address."
    )

    class Meta:
        description = "Register a new user."
        exclude = ["password"]
        model = models.User
        object_type = User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def mutate(cls, root, info, **data):
        response = super().mutate(root, info, **data)
        response.requires_confirmation = settings.ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL
        return response

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        data["metadata"] = {
            item["key"]: item["value"] for item in data.get("metadata") or []
        }
        if not settings.ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL:
            return super().clean_input(info, instance, data, input_cls=None)
        elif not data.get("redirect_url"):
            raise ValidationError(
                {
                    "redirect_url": ValidationError(
                        "This field is required.", code=AccountErrorCode.REQUIRED
                    )
                }
            )

        try:
            validate_storefront_url(data["redirect_url"])
        except ValidationError as error:
            raise ValidationError(
                {
                    "redirect_url": ValidationError(
                        error.message, code=AccountErrorCode.INVALID
                    )
                }
            )

        data["channel"] = clean_channel(
            data.get("channel"), error_class=AccountErrorCode
        ).slug

        password = data["password"]
        try:
            password_validation.validate_password(password, instance)
        except ValidationError as error:
            raise ValidationError({"password": error})

        data["language_code"] = data.get("language_code", settings.LANGUAGE_CODE)
        return super().clean_input(info, instance, data, input_cls=None)

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, user, cleaned_input):
        password = cleaned_input["password"]
        user.set_password(password)
        user.search_document = search.prepare_user_search_document_value(
            user, attach_addresses_data=False
        )
        if settings.ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL:
            user.is_active = False
            user.save()
            notifications.send_account_confirmation(
                user,
                cleaned_input["redirect_url"],
                info.context.plugins,
                channel_slug=cleaned_input["channel"],
            )
        else:
            user.save()

        account_events.customer_account_created_event(user=user)
        info.context.plugins.customer_created(customer=user)


class AccountInput(AccountBaseInput):
    default_billing_address = AddressInput(
        description="Billing address of the customer."
    )
    default_shipping_address = AddressInput(
        description="Shipping address of the customer."
    )


class AccountUpdate(BaseCustomerCreate):
    class Arguments:
        input = AccountInput(
            description="Fields required to update the account of the logged-in user.",
            required=True,
        )

    class Meta:
        description = "Updates the account of the logged-in user."
        exclude = ["password"]
        model = models.User
        object_type = User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        data["id"] = graphene.Node.to_global_id("User", user.id)
        return super().perform_mutation(root, info, **data)


class AccountRequestDeletion(BaseMutation):
    class Arguments:
        redirect_url = graphene.String(
            required=True,
            description=(
                "URL of a view where users should be redirected to "
                "delete their account. URL in RFC 1808 format."
            ),
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used to notify users. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = (
            "Sends an email with the account removal link for the logged-in user."
        )
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        user = info.context.user
        redirect_url = data["redirect_url"]
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID
            )
        channel_slug = clean_channel(
            data.get("channel"), error_class=AccountErrorCode
        ).slug
        notifications.send_account_delete_confirmation_notification(
            redirect_url, user, info.context.plugins, channel_slug=channel_slug
        )
        return AccountRequestDeletion()


class AccountDelete(ModelDeleteMutation):
    class Arguments:
        token = graphene.String(
            description=(
                "A one-time token required to remove account. "
                "Sent by email using AccountRequestDeletion mutation."
            ),
            required=True,
        )

    class Meta:
        description = "Remove user account."
        model = models.User
        object_type = User
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if instance.is_staff:
            raise ValidationError(
                "Cannot delete a staff account.",
                code=AccountErrorCode.DELETE_STAFF_ACCOUNT,
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user
        cls.clean_instance(info, user)

        token = data.pop("token")
        if not account_delete_token_generator.check_token(user, token):
            raise ValidationError(
                {"token": ValidationError(INVALID_TOKEN, code=AccountErrorCode.INVALID)}
            )

        db_id = user.id

        user.delete()
        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        user.id = db_id
        return cls.success_response(user)


class AccountAddressCreate(ModelMutation, I18nMixin):
    user = graphene.Field(
        User, description="A user instance for which the address was created."
    )

    class Arguments:
        input = AddressInput(
            description="Fields required to create address.", required=True
        )
        type = AddressTypeEnum(
            required=False,
            description=(
                "A type of address. If provided, the new address will be "
                "automatically assigned as the customer's default address "
                "of that type."
            ),
        )

    class Meta:
        description = "Create a new address for the customer."
        model = models.Address
        object_type = Address
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, root, info, **data):
        address_type = data.get("type", None)
        user = info.context.user
        cleaned_input = cls.clean_input(
            info=info, instance=Address(), data=data.get("input")
        )
        address = cls.validate_address(cleaned_input, address_type=address_type)
        cls.clean_instance(info, address)
        cls.save(info, address, cleaned_input)
        cls._save_m2m(info, address, cleaned_input)
        if address_type:
            utils.change_user_default_address(
                user, address, address_type, info.context.plugins
            )
        return AccountAddressCreate(user=user, address=address)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        super().save(info, instance, cleaned_input)
        user = info.context.user
        instance.user_addresses.add(user)
        info.context.plugins.customer_updated(user)
        user.search_document = search.prepare_user_search_document_value(user)
        user.save(update_fields=["search_document"])


class AccountAddressUpdate(BaseAddressUpdate):
    class Meta:
        description = "Updates an address of the logged-in user."
        model = models.Address
        object_type = Address
        error_type_class = AccountError
        error_type_field = "account_errors"


class AccountAddressDelete(BaseAddressDelete):
    class Meta:
        description = "Delete an address of the logged-in user."
        model = models.Address
        object_type = Address
        error_type_class = AccountError
        error_type_field = "account_errors"


class AccountSetDefaultAddress(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the address to set as default."
        )
        type = AddressTypeEnum(required=True, description="The type of address.")

    class Meta:
        description = "Sets a default address for the authenticated user."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        address = cls.get_node_or_error(info, data.get("id"), Address)
        user = info.context.user

        if not user.addresses.filter(pk=address.pk).exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "The address doesn't belong to that user.",
                        code=AccountErrorCode.INVALID,
                    )
                }
            )

        if data.get("type") == AddressTypeEnum.BILLING.value:
            address_type = AddressType.BILLING
        else:
            address_type = AddressType.SHIPPING

        utils.change_user_default_address(
            user, address, address_type, info.context.plugins
        )
        info.context.plugins.customer_updated(user)
        return cls(user=user)


class RequestEmailChange(BaseMutation):
    user = graphene.Field(User, description="A user instance.")

    class Arguments:
        password = graphene.String(required=True, description="User password.")
        new_email = graphene.String(required=True, description="New user email.")
        redirect_url = graphene.String(
            required=True,
            description=(
                "URL of a view where users should be redirected to "
                "update the email address. URL in RFC 1808 format."
            ),
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used to notify users. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = "Request email change of the logged in user."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user
        password = data["password"]
        new_email = data["new_email"]
        redirect_url = data["redirect_url"]

        if not user.check_password(password):
            raise ValidationError(
                {
                    "password": ValidationError(
                        "Password isn't valid.",
                        code=AccountErrorCode.INVALID_CREDENTIALS,
                    )
                }
            )
        if models.User.objects.filter(email=new_email).exists():
            raise ValidationError(
                {
                    "new_email": ValidationError(
                        "Email is used by other user.", code=AccountErrorCode.UNIQUE
                    )
                }
            )
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID
            )
        channel_slug = clean_channel(
            data.get("channel"),
            error_class=AccountErrorCode,
        ).slug

        token_payload = {
            "old_email": user.email,
            "new_email": new_email,
            "user_pk": user.pk,
        }
        token = create_token(token_payload, JWT_TTL_REQUEST_EMAIL_CHANGE)
        notifications.send_request_user_change_email_notification(
            redirect_url,
            user,
            new_email,
            token,
            info.context.plugins,
            channel_slug=channel_slug,
        )
        return RequestEmailChange(user=user)


class ConfirmEmailChange(BaseMutation):
    user = graphene.Field(User, description="A user instance with a new email.")

    class Arguments:
        token = graphene.String(
            description="A one-time token required to change the email.", required=True
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used to notify users. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = "Confirm the email change of the logged-in user."
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def get_token_payload(cls, token):
        try:
            payload = jwt_decode(token)
        except jwt.PyJWTError:
            raise ValidationError(
                {
                    "token": ValidationError(
                        "Invalid or expired token.",
                        code=AccountErrorCode.JWT_INVALID_TOKEN,
                    )
                }
            )
        return payload

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user
        token = data["token"]

        payload = cls.get_token_payload(token)
        new_email = payload["new_email"]
        old_email = payload["old_email"]

        if models.User.objects.filter(email=new_email).exists():
            raise ValidationError(
                {
                    "new_email": ValidationError(
                        "Email is used by other user.", code=AccountErrorCode.UNIQUE
                    )
                }
            )

        user.email = new_email
        user.search_document = search.prepare_user_search_document_value(user)
        user.save(update_fields=["email", "search_document"])

        channel_slug = clean_channel(
            data.get("channel"), error_class=AccountErrorCode
        ).slug

        assign_user_gift_cards(user)
        match_orders_with_new_user(user)

        notifications.send_user_change_email_notification(
            old_email, user, info.context.plugins, channel_slug=channel_slug
        )
        info.context.plugins.customer_updated(user)
        return ConfirmEmailChange(user=user)
