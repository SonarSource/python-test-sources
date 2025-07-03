from django.db.models import Exists, OuterRef, Sum

from ...channel.models import Channel
from ...core.db.utils import get_database_connection_name
from ...core.permissions import has_one_of_permissions
from ...core.tracing import traced_resolver
from ...order import OrderStatus
from ...order.models import Order
from ...product import models
from ...product.models import ALL_PRODUCTS_PERMISSIONS
from ..channel import ChannelQsContext
from ..core.utils import from_global_id_or_error
from ..utils import get_user_or_app_from_context
from ..utils.filters import filter_by_period


def resolve_category_by_id(id):
    return models.Category.objects.filter(pk=id).first()


def resolve_category_by_slug(slug):
    return models.Category.objects.filter(slug=slug).first()


def resolve_categories(_info, level=None, **_kwargs):
    qs = models.Category.objects.prefetch_related("children")
    if level is not None:
        qs = qs.filter(level=level)
    return qs.distinct()


def resolve_collection_by_id(info, id, channel_slug, requestor):
    return (
        models.Collection.objects.visible_to_user(requestor, channel_slug=channel_slug)
        .filter(id=id)
        .first()
    )


def resolve_collection_by_slug(info, slug, channel_slug, requestor):
    return (
        models.Collection.objects.visible_to_user(requestor, channel_slug)
        .filter(slug=slug)
        .first()
    )


def resolve_collections(info, channel_slug):
    requestor = get_user_or_app_from_context(info.context)
    qs = models.Collection.objects.visible_to_user(requestor, channel_slug)

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_digital_content_by_id(id):
    return models.DigitalContent.objects.filter(pk=id).first()


def resolve_digital_contents(_info):
    return models.DigitalContent.objects.all()


def resolve_product_by_id(info, id, channel_slug, requestor):
    database_connection_name = get_database_connection_name(info.context)
    return (
        models.Product.objects.using(database_connection_name)
        .visible_to_user(requestor, channel_slug=channel_slug)
        .filter(id=id)
        .first()
    )


def resolve_product_by_slug(info, product_slug, channel_slug, requestor):
    database_connection_name = get_database_connection_name(info.context)
    return (
        models.Product.objects.using(database_connection_name)
        .visible_to_user(requestor, channel_slug=channel_slug)
        .filter(slug=product_slug)
        .first()
    )


@traced_resolver
def resolve_products(info, requestor, channel_slug=None, **_kwargs) -> ChannelQsContext:
    database_connection_name = get_database_connection_name(info.context)
    qs = models.Product.objects.using(database_connection_name).visible_to_user(
        requestor, channel_slug
    )
    if not has_one_of_permissions(requestor, ALL_PRODUCTS_PERMISSIONS):
        channels = Channel.objects.filter(slug=str(channel_slug))
        product_channel_listings = models.ProductChannelListing.objects.filter(
            Exists(channels.filter(pk=OuterRef("channel_id"))),
            visible_in_listings=True,
        )
        qs = qs.filter(
            Exists(product_channel_listings.filter(product_id=OuterRef("pk")))
        )
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


@traced_resolver
def resolve_variant_by_id(
    info, id, channel_slug, requestor, requestor_has_access_to_all
):
    visible_products = models.Product.objects.visible_to_user(
        requestor, channel_slug
    ).values_list("pk", flat=True)
    qs = models.ProductVariant.objects.filter(product__id__in=visible_products)
    if not requestor_has_access_to_all:
        qs = qs.available_in_channel(channel_slug)
    return qs.filter(pk=id).first()


def resolve_product_type_by_id(id):
    return models.ProductType.objects.filter(pk=id).first()


def resolve_product_types(_info, **_kwargs):
    return models.ProductType.objects.all()


@traced_resolver
def resolve_product_variant_by_sku(
    info, sku, channel_slug, requestor, requestor_has_access_to_all
):
    visible_products = models.Product.objects.visible_to_user(requestor, channel_slug)
    qs = models.ProductVariant.objects.filter(product__id__in=visible_products)
    if not requestor_has_access_to_all:
        visible_products = visible_products.annotate_visible_in_listings(
            channel_slug
        ).exclude(visible_in_listings=False)
        qs = qs.filter(product__in=visible_products).available_in_channel(channel_slug)
    return qs.filter(sku=sku).first()


@traced_resolver
def resolve_product_variants(
    info, requestor_has_access_to_all, requestor, ids=None, channel_slug=None
) -> ChannelQsContext:
    visible_products = models.Product.objects.visible_to_user(requestor, channel_slug)
    qs = models.ProductVariant.objects.filter(product__id__in=visible_products)

    if not requestor_has_access_to_all:
        visible_products = visible_products.annotate_visible_in_listings(
            channel_slug
        ).exclude(visible_in_listings=False)
        qs = qs.filter(product__in=visible_products).available_in_channel(channel_slug)
    if ids:
        db_ids = [
            from_global_id_or_error(node_id, "ProductVariant")[1] for node_id in ids
        ]
        qs = qs.filter(pk__in=db_ids)
    return ChannelQsContext(qs=qs, channel_slug=channel_slug)


def resolve_report_product_sales(period, channel_slug) -> ChannelQsContext:
    qs = models.ProductVariant.objects.all()

    # filter by period
    qs = filter_by_period(qs, period, "order_lines__order__created")

    # annotate quantity
    qs = qs.annotate(quantity_ordered=Sum("order_lines__quantity"))

    # filter by channel and order status
    channels = Channel.objects.filter(slug=channel_slug).values("pk")
    exclude_status = [OrderStatus.DRAFT, OrderStatus.CANCELED]
    orders = Order.objects.exclude(status__in=exclude_status).filter(
        Exists(channels.filter(pk=OuterRef("channel_id")).values("pk"))
    )
    qs = qs.filter(
        Exists(orders.filter(pk=OuterRef("order_lines__order_id"))),
        quantity_ordered__isnull=False,
    )

    # order by quantity ordered
    qs = qs.order_by("-quantity_ordered")

    return ChannelQsContext(qs=qs, channel_slug=channel_slug)
