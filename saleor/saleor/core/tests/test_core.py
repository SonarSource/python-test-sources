import io
from contextlib import redirect_stdout
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import pytest
from django.core.files.storage import default_storage
from django.core.management import CommandError, call_command
from django.db.utils import DataError
from django.templatetags.static import static
from django.test import RequestFactory, override_settings
from django_countries.fields import Country

from ...account.models import Address, User
from ...account.utils import create_superuser
from ...channel.models import Channel
from ...discount.models import Sale, SaleChannelListing, Voucher, VoucherChannelListing
from ...giftcard.models import GiftCard, GiftCardEvent
from ...order.models import Order, OrderLine
from ...product import ProductTypeKind
from ...product.models import ProductMedia, ProductType
from ...shipping.models import ShippingZone
from ..storages import S3MediaStorage
from ..templatetags.placeholder import placeholder
from ..utils import (
    build_absolute_uri,
    create_thumbnails,
    delete_versatile_image,
    generate_unique_slug,
    get_client_ip,
    get_currency_for_country,
    random_data,
)

type_schema = {
    "Vegetable": {
        "category": {"name": "Food", "image_name": "books.jpg"},
        "product_attributes": {
            "Sweetness": ["Sweet", "Sour"],
            "Healthiness": ["Healthy", "Not really"],
        },
        "variant_attributes": {"GMO": ["Yes", "No"]},
        "images_dir": "candy/",
        "is_shipping_required": True,
    }
}


@pytest.mark.parametrize(
    "ip_address, expected_ip",
    [
        ("83.0.0.1", "83.0.0.1"),
        ("::1", "::1"),
        ("256.0.0.1", "127.0.0.1"),
        ("1:1:1", "127.0.0.1"),
        ("invalid,8.8.8.8", "8.8.8.8"),
        (None, "127.0.0.1"),
    ],
)
def test_get_client_ip(ip_address, expected_ip):
    """Test providing a valid IP in X-Forwarded-For returns the valid IP.
    Otherwise, if no valid IP were found, returns the requester's IP.
    """
    expected_ip = expected_ip
    headers = {"HTTP_X_FORWARDED_FOR": ip_address} if ip_address else {}
    request = RequestFactory(**headers).get("/")
    assert get_client_ip(request) == expected_ip


@pytest.mark.parametrize(
    "country, expected_currency",
    [(Country("PL"), "PLN"), (Country("US"), "USD"), (Country("GB"), "GBP")],
)
def test_get_currency_for_country(country, expected_currency, monkeypatch):
    currency = get_currency_for_country(country.code)
    assert currency == expected_currency


def test_create_superuser(db, client, media_root):
    credentials = {"email": "admin@example.com", "password": "admin"}
    # Test admin creation
    assert User.objects.all().count() == 0
    create_superuser(credentials)
    assert User.objects.all().count() == 1
    admin = User.objects.all().first()
    assert admin.is_superuser
    assert not admin.avatar
    # Test duplicating
    create_superuser(credentials)
    assert User.objects.all().count() == 1


def test_create_shipping_zones(db):
    assert ShippingZone.objects.all().count() == 0
    for _ in random_data.create_shipping_zones():
        pass
    assert ShippingZone.objects.all().count() == 5


def test_create_channels(db):
    assert Channel.objects.all().count() == 0
    for _ in random_data.create_channels():
        pass
    assert Channel.objects.all().count() == 2
    assert Channel.objects.get(slug="channel-pln")


@override_settings(DEFAULT_CHANNEL_SLUG="test-slug")
def test_create_channels_with_default_channel_slug(db):
    assert Channel.objects.all().count() == 0
    for _ in random_data.create_channels():
        pass
    assert Channel.objects.all().count() == 2
    assert Channel.objects.get(slug="test-slug")


def test_create_fake_user(db):
    assert User.objects.all().count() == 0
    random_data.create_fake_user("password")
    assert User.objects.all().count() == 1
    user = User.objects.all().first()
    assert not user.is_superuser


def test_create_fake_users(db):
    how_many = 5
    for _ in random_data.create_users("password", how_many):
        pass
    assert User.objects.all().count() == 5


def test_create_address(db):
    assert not Address.objects.exists()
    random_data.create_address()
    assert Address.objects.all().count() == 1


def test_create_fake_order(db, monkeypatch, image, media_root, warehouse):
    # Tests shouldn't depend on images present in placeholder folder
    monkeypatch.setattr(
        "saleor.core.utils.random_data.get_image", Mock(return_value=image)
    )
    for _ in random_data.create_channels():
        pass
    for _ in random_data.create_shipping_zones():
        pass
    for _ in random_data.create_users("password", 3):
        pass
    for msg in random_data.create_page_type():
        pass
    for msg in random_data.create_pages():
        pass
    random_data.create_products_by_schema("/", False)
    how_many_orders = 2
    for _ in random_data.create_orders(how_many_orders):
        pass
    assert Order.objects.all().count() == 2

    how_many_preorder_orders = 1
    for _ in random_data.create_preorder_orders(how_many_preorder_orders):
        pass
    assert Order.objects.count() == how_many_orders + how_many_preorder_orders
    assert OrderLine.objects.filter(variant__is_preorder=True).exists()


def test_create_product_sales(db):
    how_many = 5
    channel_count = 0
    for _ in random_data.create_channels():
        channel_count += 1
    for _ in random_data.create_product_sales(how_many):
        pass
    assert Sale.objects.all().count() == how_many
    assert SaleChannelListing.objects.all().count() == how_many * channel_count


def test_create_vouchers(db):
    voucher_count = 3
    channel_count = 0
    for _ in random_data.create_channels():
        channel_count += 1
    assert Voucher.objects.all().count() == 0
    for _ in random_data.create_vouchers():
        pass
    assert Voucher.objects.all().count() == voucher_count
    assert VoucherChannelListing.objects.all().count() == voucher_count * channel_count


def test_create_gift_card(
    db, product, shippable_gift_card_product, customer_user, staff_user, order
):
    product = shippable_gift_card_product
    product.name = "Gift card"
    product.save(update_fields=["name"])

    amount = 5
    assert GiftCard.objects.count() == 0
    assert GiftCardEvent.objects.count() == 0
    for _ in random_data.create_gift_cards(amount):
        pass
    assert GiftCard.objects.count() == amount * 2
    assert GiftCardEvent.objects.count() == amount * 2


@override_settings(VERSATILEIMAGEFIELD_SETTINGS={"create_images_on_demand": False})
def test_create_thumbnails(product_with_image, settings, monkeypatch):
    monkeypatch.setattr("django.core.cache.cache.get", Mock(return_value=None))
    sizeset = settings.VERSATILEIMAGEFIELD_RENDITION_KEY_SETS["products"]
    product_image = product_with_image.media.first()

    # There's no way to list images created by versatile prewarmer
    # So we delete all created thumbnails/crops and count them
    log_deleted_images = io.StringIO()
    with redirect_stdout(log_deleted_images):
        product_image.image.delete_all_created_images()
    log_deleted_images = log_deleted_images.getvalue()
    # Image didn't have any thumbnails/crops created, so there's no log
    assert not log_deleted_images

    create_thumbnails(product_image.pk, ProductMedia, "products")
    log_deleted_images = io.StringIO()
    with redirect_stdout(log_deleted_images):
        product_image.image.delete_all_created_images()
    log_deleted_images = log_deleted_images.getvalue()

    for image_name, method_size in sizeset:
        method, size = method_size.split("__")
        if method == "crop":
            assert product_image.image.crop[size].name in log_deleted_images
        elif method == "thumbnail":
            assert (
                product_image.image.thumbnail[size].name in log_deleted_images
            )  # noqa


@patch("storages.backends.s3boto3.S3Boto3Storage")
def test_storages_set_s3_bucket_domain(storage, settings):
    settings.AWS_MEDIA_BUCKET_NAME = "media-bucket"
    settings.AWS_MEDIA_CUSTOM_DOMAIN = "media-bucket.example.org"
    storage = S3MediaStorage()
    assert storage.bucket_name == "media-bucket"
    assert storage.custom_domain == "media-bucket.example.org"


@patch("storages.backends.s3boto3.S3Boto3Storage")
def test_storages_not_setting_s3_bucket_domain(storage, settings):
    settings.AWS_MEDIA_BUCKET_NAME = "media-bucket"
    settings.AWS_MEDIA_CUSTOM_DOMAIN = None
    storage = S3MediaStorage()
    assert storage.bucket_name == "media-bucket"
    assert storage.custom_domain is None


def test_build_absolute_uri(site_settings, settings):
    # Case when we are using external service for storing static files,
    # eg. Amazon s3
    url = "https://example.com/static/images/image.jpg"
    assert build_absolute_uri(location=url) == url

    # Case when static url is resolved to relative url
    logo_url = build_absolute_uri(static("images/close.svg"))
    protocol = "https" if settings.ENABLE_SSL else "http"
    current_url = "%s://%s" % (protocol, site_settings.site.domain)
    logo_location = urljoin(current_url, static("images/close.svg"))
    assert logo_url == logo_location


def test_delete_sort_order_with_null_value(menu_item):
    """Ensures there is no error when trying to delete a sortable item,
    which triggers a shifting of the sort orders--which can be null."""

    menu_item.sort_order = None
    menu_item.save(update_fields=["sort_order"])
    menu_item.delete()


def test_placeholder(settings):
    size = 60
    result = placeholder(size)
    assert result == "/static/" + settings.PLACEHOLDER_IMAGES[size]


@pytest.mark.parametrize(
    "product_name, slug_result",
    [
        ("Paint", "paint"),
        ("paint", "paint-3"),
        ("Default Type", "default-type"),
        ("default type", "default-type-2"),
        ("Shirt", "shirt"),
        ("40.5", "405-2"),
        ("FM1+", "fm1-2"),
        ("زيوت", "زيوت"),
        ("わたし-わ にっぽん です", "わたし-わ-にっぽん-です-2"),
    ],
)
def test_generate_unique_slug_with_slugable_field(
    product_type, product_name, slug_result
):
    product_names_and_slugs = [
        ("Paint", "paint"),
        ("Paint blue", "paint-blue"),
        ("Paint test", "paint-2"),
        ("405", "405"),
        ("FM1", "fm1"),
        ("わたし わ にっぽん です", "わたし-わ-にっぽん-です"),
    ]
    for name, slug in product_names_and_slugs:
        ProductType.objects.create(
            name=name,
            slug=slug,
            kind=ProductTypeKind.NORMAL,
        )

    instance, _ = ProductType.objects.get_or_create(name=product_name)
    result = generate_unique_slug(instance, instance.name)
    assert result == slug_result


def test_generate_unique_slug_for_slug_with_max_characters_number(category):
    slug = "a" * 256
    result = generate_unique_slug(category, slug)
    category.slug = result
    with pytest.raises(DataError):
        category.save()


def test_generate_unique_slug_non_slugable_value_and_slugable_field(category):
    with pytest.raises(Exception):
        generate_unique_slug(category)


@override_settings(DEBUG=False)
def test_cleardb_exits_with_debug_off():
    with pytest.raises(CommandError):
        call_command("cleardb")


@override_settings(DEBUG=False)
def test_cleardb_passes_with_force_flag_in_debug_off():
    call_command("cleardb", "--force")


@override_settings(DEBUG=True)
def test_cleardb_delete_staff_parameter(staff_user):
    # cleardb without delete_staff flag keeps staff users
    call_command("cleardb")
    staff_user.refresh_from_db()

    # when the flag is present staff user should be deleted
    call_command("cleardb", delete_staff=True)
    with pytest.raises(User.DoesNotExist):
        staff_user.refresh_from_db()


@override_settings(DEBUG=True)
def test_cleardb_preserves_data(admin_user, app, site_settings, staff_user):
    call_command("cleardb")
    # These shouldn't be deleted when running `cleardb`.
    admin_user.refresh_from_db()
    app.refresh_from_db()
    site_settings.refresh_from_db()
    staff_user.refresh_from_db()


def test_delete_versatile_image(product_with_image, media_root):
    # given
    media = product_with_image.media.first()
    thumb_200x200 = media.image.thumbnail["200x200"].name
    thumb_400x400 = media.image.thumbnail["400x400"].name
    img_name = media.image.name

    assert default_storage.exists(img_name)
    assert default_storage.exists(thumb_200x200)
    assert default_storage.exists(thumb_400x400)

    # when
    delete_versatile_image(media.image)

    # then
    assert not default_storage.exists(img_name)
    assert not default_storage.exists(thumb_400x400)
    assert not default_storage.exists(thumb_400x400)
