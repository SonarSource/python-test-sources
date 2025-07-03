import graphene

from ...core.permissions import GiftcardPermissions, OrderPermissions
from ..decorators import permission_required
from ..translations.mutations import ShopSettingsTranslate
from .mutations import (
    GiftCardSettingsUpdate,
    OrderSettingsUpdate,
    ShopAddressUpdate,
    ShopDomainUpdate,
    ShopFetchTaxRates,
    ShopSettingsUpdate,
    StaffNotificationRecipientCreate,
    StaffNotificationRecipientDelete,
    StaffNotificationRecipientUpdate,
)
from .types import GiftCardSettings, OrderSettings, Shop


class ShopQueries(graphene.ObjectType):
    shop = graphene.Field(
        Shop,
        description="Return information about the shop.",
        required=True,
    )
    order_settings = graphene.Field(
        OrderSettings, description="Order related settings from site settings."
    )
    gift_card_settings = graphene.Field(
        GiftCardSettings,
        description="Gift card related settings from site settings.",
        required=True,
    )

    def resolve_shop(self, _info):
        return Shop()

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_order_settings(self, info, *args, **_kwargs):
        return info.context.site.settings

    @permission_required(GiftcardPermissions.MANAGE_GIFT_CARD)
    def resolve_gift_card_settings(self, info, *args, **_kwargs):
        return info.context.site.settings


class ShopMutations(graphene.ObjectType):
    staff_notification_recipient_create = StaffNotificationRecipientCreate.Field()
    staff_notification_recipient_update = StaffNotificationRecipientUpdate.Field()
    staff_notification_recipient_delete = StaffNotificationRecipientDelete.Field()

    shop_domain_update = ShopDomainUpdate.Field()
    shop_settings_update = ShopSettingsUpdate.Field()
    shop_fetch_tax_rates = ShopFetchTaxRates.Field()
    shop_settings_translate = ShopSettingsTranslate.Field()
    shop_address_update = ShopAddressUpdate.Field()

    order_settings_update = OrderSettingsUpdate.Field()
    gift_card_settings_update = GiftCardSettingsUpdate.Field()
