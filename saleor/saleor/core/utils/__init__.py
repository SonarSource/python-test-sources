import os
import socket
from typing import TYPE_CHECKING, Optional, Type, Union
from urllib.parse import urljoin

from babel.numbers import get_territory_currencies
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Model
from django.utils.encoding import iri_to_uri
from django.utils.text import slugify
from django_prices_openexchangerates import exchange_currency
from prices import MoneyRange
from versatileimagefield.image_warmer import VersatileImageFieldWarmer

task_logger = get_task_logger(__name__)


if TYPE_CHECKING:
    # flake8: noqa: F401
    from django.utils.safestring import SafeText


def build_absolute_uri(location: str) -> Optional[str]:
    """Create absolute uri from location.

    If provided location is absolute uri by itself, it returns unchanged value,
    otherwise if provided location is relative, absolute uri is built and returned.
    """
    host = Site.objects.get_current().domain
    protocol = "https" if settings.ENABLE_SSL else "http"
    current_uri = "%s://%s" % (protocol, host)
    location = urljoin(current_uri, location)
    return iri_to_uri(location)


def get_client_ip(request):
    """Retrieve the IP address from the request data.

    Tries to get a valid IP address from X-Forwarded-For, if the user is hiding behind
    a transparent proxy or if the server is behind a proxy.

    If no forwarded IP was provided or all of them are invalid,
    it fallback to the requester IP.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ips = ip.split(",")
    for ip in ips:
        if is_valid_ipv4(ip) or is_valid_ipv6(ip):
            return ip
    return request.META.get("REMOTE_ADDR", None)


def is_valid_ipv4(ip: str) -> bool:
    """Check whether the passed IP is a valid V4 IP address."""
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except socket.error:
        return False
    return True


def is_valid_ipv6(ip: str) -> bool:
    """Check whether the passed IP is a valid V6 IP address."""
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False
    return True


def get_currency_for_country(country_code: str):
    currencies = get_territory_currencies(country_code)
    if currencies:
        return currencies[0]
    return os.environ.get("DEFAULT_CURRENCY", "USD")


def to_local_currency(price, currency):
    if price is None:
        return None
    if not settings.OPENEXCHANGERATES_API_KEY:
        return None
    if isinstance(price, MoneyRange):
        from_currency = price.start.currency
    else:
        from_currency = price.currency
    if currency != from_currency:
        try:
            return exchange_currency(price, currency)
        except ValueError:
            pass
    return None


def create_thumbnails(pk, model, size_set, image_attr=None):
    instance = model.objects.get(pk=pk)
    if not image_attr:
        image_attr = "image"
    image_instance = getattr(instance, image_attr)
    if image_instance.name == "":
        # There is no file, skip processing
        return
    warmer = VersatileImageFieldWarmer(
        instance_or_queryset=instance, rendition_key_set=size_set, image_attr=image_attr
    )
    task_logger.info("Creating thumbnails for %s", pk)
    num_created, failed_to_create = warmer.warm()
    if num_created:
        task_logger.info("Created %d thumbnails", num_created)
    if failed_to_create:
        task_logger.error(
            "Failed to generate thumbnails", extra={"paths": failed_to_create}
        )


def generate_unique_slug(
    instance: Type[Model],
    slugable_value: str,
    slug_field_name: str = "slug",
) -> str:
    """Create unique slug for model instance.

    The function uses `django.utils.text.slugify` to generate a slug from
    the `slugable_value` of model field. If the slug already exists it adds
    a numeric suffix and increments it until a unique value is found.

    Args:
        instance: model instance for which slug is created
        slugable_value: value used to create slug
        slug_field_name: name of slug field in instance model

    """
    slug = slugify(slugable_value, allow_unicode=True)
    unique_slug: Union["SafeText", str] = slug

    ModelClass = instance.__class__
    extension = 1

    search_field = f"{slug_field_name}__iregex"
    pattern = rf"{slug}-\d+$|{slug}$"
    slug_values = (
        ModelClass._default_manager.filter(**{search_field: pattern})  # type: ignore
        .exclude(pk=instance.pk)
        .values_list(slug_field_name, flat=True)
    )

    while unique_slug in slug_values:
        extension += 1
        unique_slug = f"{slug}-{extension}"

    return unique_slug


def delete_versatile_image(image):
    image.delete_all_created_images()
    image.delete(save=False)
