from typing import List

import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth import models as auth_models
from graphene import relay
from graphene_federation import key

from ...account import models
from ...checkout.utils import get_user_checkout
from ...core.exceptions import PermissionDenied
from ...core.permissions import AccountPermissions, AppPermission, OrderPermissions
from ...core.tracing import traced_resolver
from ...order import OrderStatus
from ..account.utils import requestor_has_access
from ..app.dataloaders import AppByIdLoader
from ..app.types import App
from ..checkout.dataloaders import CheckoutByUserAndChannelLoader, CheckoutByUserLoader
from ..checkout.types import Checkout
from ..core.connection import CountableConnection, create_connection_slice
from ..core.descriptions import DEPRECATED_IN_3X_FIELD
from ..core.enums import LanguageCodeEnum
from ..core.federation import resolve_federation_references
from ..core.fields import ConnectionField
from ..core.scalars import UUID
from ..core.types import CountryDisplay, Image, ModelObjectType, Permission
from ..core.utils import from_global_id_or_error, str_to_enum
from ..decorators import one_of_permissions_required, permission_required
from ..giftcard.dataloaders import GiftCardsByUserLoader
from ..meta.types import ObjectWithMetadata
from ..order.dataloaders import OrderLineByIdLoader, OrdersByUserLoader
from ..utils import format_permissions_for_display, get_user_or_app_from_context
from .dataloaders import CustomerEventsByUserLoader
from .enums import CountryCodeEnum, CustomerEventsEnum
from .utils import can_user_manage_group, get_groups_which_user_can_manage


class AddressInput(graphene.InputObjectType):
    first_name = graphene.String(description="Given name.")
    last_name = graphene.String(description="Family name.")
    company_name = graphene.String(description="Company or organization.")
    street_address_1 = graphene.String(description="Address.")
    street_address_2 = graphene.String(description="Address.")
    city = graphene.String(description="City.")
    city_area = graphene.String(description="District.")
    postal_code = graphene.String(description="Postal code.")
    country = CountryCodeEnum(description="Country.")
    country_area = graphene.String(description="State or province.")
    phone = graphene.String(description="Phone number.")


@key(fields="id")
class Address(ModelObjectType):
    id = graphene.GlobalID(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    company_name = graphene.String(required=True)
    street_address_1 = graphene.String(required=True)
    street_address_2 = graphene.String(required=True)
    city = graphene.String(required=True)
    city_area = graphene.String(required=True)
    postal_code = graphene.String(required=True)
    country = graphene.Field(
        CountryDisplay, required=True, description="Shop's default country."
    )
    country_area = graphene.String(required=True)
    phone = graphene.String()
    is_default_shipping_address = graphene.Boolean(
        required=False, description="Address is user's default shipping address."
    )
    is_default_billing_address = graphene.Boolean(
        required=False, description="Address is user's default billing address."
    )

    class Meta:
        description = "Represents user address data."
        interfaces = [relay.Node]
        model = models.Address

    @staticmethod
    def resolve_country(root: models.Address, _info):
        return CountryDisplay(code=root.country.code, country=root.country.name)

    @staticmethod
    def resolve_is_default_shipping_address(root: models.Address, _info):
        """Look if the address is the default shipping address of the user.

        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(root, "user_default_shipping_address_pk"):
            return None

        user_default_shipping_address_pk = getattr(
            root, "user_default_shipping_address_pk"
        )
        if user_default_shipping_address_pk == root.pk:
            return True
        return False

    @staticmethod
    def resolve_is_default_billing_address(root: models.Address, _info):
        """Look if the address is the default billing address of the user.

        This field is added through annotation when using the
        `resolve_addresses` resolver. It's invalid for
        `resolve_default_shipping_address` and
        `resolve_default_billing_address`
        """
        if not hasattr(root, "user_default_billing_address_pk"):
            return None

        user_default_billing_address_pk = getattr(
            root, "user_default_billing_address_pk"
        )
        if user_default_billing_address_pk == root.pk:
            return True
        return False

    @staticmethod
    def __resolve_references(roots: List["Address"], info, **_kwargs):
        from .resolvers import resolve_addresses

        root_ids = [root.id for root in roots]
        addresses = {
            address.id: address for address in resolve_addresses(info, root_ids)
        }

        result = []
        for root_id in root_ids:
            _, root_id = from_global_id_or_error(root_id, Address)
            result.append(addresses.get(int(root_id)))
        return result


class CustomerEvent(ModelObjectType):
    id = graphene.GlobalID(required=True)
    date = graphene.types.datetime.DateTime(
        description="Date when event happened at in ISO 8601 format."
    )
    type = CustomerEventsEnum(description="Customer event type.")
    user = graphene.Field(lambda: User, description="User who performed the action.")
    app = graphene.Field(App, description="App that performed the action.")
    message = graphene.String(description="Content of the event.")
    count = graphene.Int(description="Number of objects concerned by the event.")
    order = graphene.Field(
        "saleor.graphql.order.types.Order", description="The concerned order."
    )
    order_line = graphene.Field(
        "saleor.graphql.order.types.OrderLine", description="The concerned order line."
    )

    class Meta:
        description = "History log of the customer."
        interfaces = [relay.Node]
        model = models.CustomerEvent

    @staticmethod
    def resolve_user(root: models.CustomerEvent, info):
        user = info.context.user
        if (
            user == root.user
            or user.has_perm(AccountPermissions.MANAGE_USERS)
            or user.has_perm(AccountPermissions.MANAGE_STAFF)
        ):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_app(root: models.CustomerEvent, info):
        requestor = get_user_or_app_from_context(info.context)
        if requestor_has_access(requestor, root.user, AppPermission.MANAGE_APPS):
            return (
                AppByIdLoader(info.context).load(root.app_id) if root.app_id else None
            )
        raise PermissionDenied()

    @staticmethod
    def resolve_message(root: models.CustomerEvent, _info):
        return root.parameters.get("message", None)

    @staticmethod
    def resolve_count(root: models.CustomerEvent, _info):
        return root.parameters.get("count", None)

    @staticmethod
    def resolve_order_line(root: models.CustomerEvent, info):
        if "order_line_pk" in root.parameters:
            return OrderLineByIdLoader(info.context).load(
                root.parameters["order_line_pk"]
            )
        return None


class UserPermission(Permission):
    source_permission_groups = graphene.List(
        graphene.NonNull("saleor.graphql.account.types.Group"),
        description="List of user permission groups which contains this permission.",
        user_id=graphene.Argument(
            graphene.ID,
            description="ID of user whose groups should be returned.",
            required=True,
        ),
        required=False,
    )

    @traced_resolver
    def resolve_source_permission_groups(root: Permission, _info, user_id, **_kwargs):
        _type, user_id = from_global_id_or_error(user_id, only_type="User")
        groups = auth_models.Group.objects.filter(
            user__pk=user_id, permissions__name=root.name
        )
        return groups


@key(fields="id")
@key(fields="email")
class User(ModelObjectType):
    id = graphene.GlobalID(required=True)
    email = graphene.String(required=True)
    first_name = graphene.String(required=True)
    last_name = graphene.String(required=True)
    is_staff = graphene.Boolean(required=True)
    is_active = graphene.Boolean(required=True)
    addresses = graphene.List(Address, description="List of all user's addresses.")
    checkout = graphene.Field(
        Checkout,
        description="Returns the last open checkout of this user.",
        deprecation_reason=(
            f"{DEPRECATED_IN_3X_FIELD} "
            "Use the `checkout_tokens` field to fetch the user checkouts."
        ),
    )
    checkout_tokens = graphene.List(
        graphene.NonNull(UUID),
        description="Returns the checkout UUID's assigned to this user.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    gift_cards = ConnectionField(
        "saleor.graphql.giftcard.types.GiftCardCountableConnection",
        description="List of the user gift cards.",
    )
    note = graphene.String(description="A note about the customer.")
    orders = ConnectionField(
        "saleor.graphql.order.types.OrderCountableConnection",
        description="List of user's orders.",
    )
    user_permissions = graphene.List(
        UserPermission, description="List of user's permissions."
    )
    permission_groups = graphene.List(
        "saleor.graphql.account.types.Group",
        description="List of user's permission groups.",
    )
    editable_groups = graphene.List(
        "saleor.graphql.account.types.Group",
        description="List of user's permission groups which user can manage.",
    )
    avatar = graphene.Field(Image, size=graphene.Int(description="Size of the avatar."))
    events = graphene.List(
        CustomerEvent, description="List of events associated with the user."
    )
    stored_payment_sources = graphene.List(
        "saleor.graphql.payment.types.PaymentSource",
        description="List of stored payment sources.",
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
    )
    language_code = graphene.Field(
        LanguageCodeEnum, description="User language code.", required=True
    )
    default_shipping_address = graphene.Field(Address)
    default_billing_address = graphene.Field(Address)

    last_login = graphene.DateTime()
    date_joined = graphene.DateTime(required=True)

    class Meta:
        description = "Represents user data."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = get_user_model()

    @staticmethod
    def resolve_addresses(root: models.User, _info, **_kwargs):
        return root.addresses.annotate_default(root).all()  # type: ignore

    @staticmethod
    def resolve_checkout(root: models.User, _info, **_kwargs):
        return get_user_checkout(root)

    @staticmethod
    @traced_resolver
    def resolve_checkout_tokens(root: models.User, info, channel=None, **_kwargs):
        def return_checkout_tokens(checkouts):
            if not checkouts:
                return []
            checkout_global_ids = []
            for checkout in checkouts:
                checkout_global_ids.append(checkout.token)
            return checkout_global_ids

        if not channel:
            return (
                CheckoutByUserLoader(info.context)
                .load(root.id)
                .then(return_checkout_tokens)
            )
        return (
            CheckoutByUserAndChannelLoader(info.context)
            .load((root.id, channel))
            .then(return_checkout_tokens)
        )

    @staticmethod
    def resolve_gift_cards(root: models.User, info, **kwargs):
        from ..giftcard.types import GiftCardCountableConnection

        def _resolve_gift_cards(gift_cards):
            return create_connection_slice(
                gift_cards, info, kwargs, GiftCardCountableConnection
            )

        return (
            GiftCardsByUserLoader(info.context).load(root.id).then(_resolve_gift_cards)
        )

    @staticmethod
    def resolve_user_permissions(root: models.User, _info, **_kwargs):
        from .resolvers import resolve_permissions

        return resolve_permissions(root)

    @staticmethod
    def resolve_permission_groups(root: models.User, _info, **_kwargs):
        return root.groups.all()

    @staticmethod
    def resolve_editable_groups(root: models.User, _info, **_kwargs):
        return get_groups_which_user_can_manage(root)

    @staticmethod
    @one_of_permissions_required(
        [AccountPermissions.MANAGE_USERS, AccountPermissions.MANAGE_STAFF]
    )
    def resolve_note(root: models.User, info):
        return root.note

    @staticmethod
    @one_of_permissions_required(
        [AccountPermissions.MANAGE_USERS, AccountPermissions.MANAGE_STAFF]
    )
    def resolve_events(root: models.User, info):
        return CustomerEventsByUserLoader(info.context).load(root.id)

    @staticmethod
    def resolve_orders(root: models.User, info, **kwargs):
        from ..order.types import OrderCountableConnection

        def _resolve_orders(orders):
            requester = get_user_or_app_from_context(info.context)
            if not requester.has_perm(OrderPermissions.MANAGE_ORDERS):
                orders = list(
                    filter(lambda order: order.status != OrderStatus.DRAFT, orders)
                )

            return create_connection_slice(
                orders, info, kwargs, OrderCountableConnection
            )

        return OrdersByUserLoader(info.context).load(root.id).then(_resolve_orders)

    @staticmethod
    def resolve_avatar(root: models.User, info, size=None, **_kwargs):
        if root.avatar:
            return Image.get_adjusted(
                image=root.avatar,
                alt=None,
                size=size,
                rendition_key_set="user_avatars",
                info=info,
            )

    @staticmethod
    def resolve_stored_payment_sources(root: models.User, info, channel=None):
        from .resolvers import resolve_payment_sources

        if root == info.context.user:
            return resolve_payment_sources(info, root, channel_slug=channel)
        raise PermissionDenied()

    @staticmethod
    def resolve_language_code(root, _info, **_kwargs):
        return LanguageCodeEnum[str_to_enum(root.language_code)]

    @staticmethod
    def __resolve_references(roots: List["User"], info, **_kwargs):
        from .resolvers import resolve_users

        ids = set()
        emails = set()
        for root in roots:
            if root.id is not None:
                ids.add(root.id)
            else:
                emails.add(root.email)

        users = list(resolve_users(info, ids=ids, emails=emails))
        users_by_id = {user.id: user for user in users}
        users_by_email = {user.email: user for user in users}

        results = []
        for root in roots:
            if root.id is not None:
                _, user_id = from_global_id_or_error(root.id, User)
                results.append(users_by_id.get(int(user_id)))
            else:
                results.append(users_by_email.get(root.email))
        return results


class UserCountableConnection(CountableConnection):
    class Meta:
        node = User


class ChoiceValue(graphene.ObjectType):
    raw = graphene.String()
    verbose = graphene.String()


class AddressValidationData(graphene.ObjectType):
    country_code = graphene.String()
    country_name = graphene.String()
    address_format = graphene.String()
    address_latin_format = graphene.String()
    allowed_fields = graphene.List(graphene.String)
    required_fields = graphene.List(graphene.String)
    upper_fields = graphene.List(graphene.String)
    country_area_type = graphene.String()
    country_area_choices = graphene.List(ChoiceValue)
    city_type = graphene.String()
    city_choices = graphene.List(ChoiceValue)
    city_area_type = graphene.String()
    city_area_choices = graphene.List(ChoiceValue)
    postal_code_type = graphene.String()
    postal_code_matchers = graphene.List(graphene.String)
    postal_code_examples = graphene.List(graphene.String)
    postal_code_prefix = graphene.String()


class StaffNotificationRecipient(graphene.ObjectType):
    id = graphene.ID(required=True)
    user = graphene.Field(
        User,
        description="Returns a user subscribed to email notifications.",
        required=False,
    )
    email = graphene.String(
        description=(
            "Returns email address of a user subscribed to email notifications."
        ),
        required=False,
    )
    active = graphene.Boolean(description="Determines if a notification active.")

    class Meta:
        description = (
            "Represents a recipient of email notifications send by Saleor, "
            "such as notifications about new orders. Notifications can be "
            "assigned to staff users or arbitrary email addresses."
        )
        interfaces = [relay.Node]
        model = models.StaffNotificationRecipient

    @staticmethod
    def get_node(info, id):
        try:
            return models.StaffNotificationRecipient.objects.get(pk=id)
        except models.StaffNotificationRecipient.DoesNotExist:
            return None

    @staticmethod
    def resolve_user(root: models.StaffNotificationRecipient, info):
        user = info.context.user
        if user == root.user or user.has_perm(AccountPermissions.MANAGE_STAFF):
            return root.user
        raise PermissionDenied()

    @staticmethod
    def resolve_email(root: models.StaffNotificationRecipient, _info):
        return root.get_email()


@key(fields="id")
class Group(ModelObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String(required=True)
    users = graphene.List(User, description="List of group users")
    permissions = graphene.List(Permission, description="List of group permissions")
    user_can_manage = graphene.Boolean(
        required=True,
        description=(
            "True, if the currently authenticated user has rights to manage a group."
        ),
    )

    class Meta:
        description = "Represents permission group data."
        interfaces = [relay.Node]
        model = auth_models.Group

    @staticmethod
    @permission_required(AccountPermissions.MANAGE_STAFF)
    def resolve_users(root: auth_models.Group, _info):
        return root.user_set.all()

    @staticmethod
    def resolve_permissions(root: auth_models.Group, _info):
        permissions = root.permissions.prefetch_related("content_type").order_by(
            "codename"
        )
        return format_permissions_for_display(permissions)

    @staticmethod
    def resolve_user_can_manage(root: auth_models.Group, info):
        user = info.context.user
        return can_user_manage_group(user, root)

    @staticmethod
    def __resolve_references(roots: List["Group"], info, **_kwargs):
        from .resolvers import resolve_permission_groups

        requestor = get_user_or_app_from_context(info.context)
        if not requestor.has_perm(AccountPermissions.MANAGE_STAFF):
            qs = auth_models.Group.objects.none()
        else:
            qs = resolve_permission_groups(info)

        return resolve_federation_references(Group, roots, qs)


class GroupCountableConnection(CountableConnection):
    class Meta:
        node = Group
