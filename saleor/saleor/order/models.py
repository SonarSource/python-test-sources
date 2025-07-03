from decimal import Decimal
from operator import attrgetter
from re import match
from typing import Optional
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import JSONField  # type: ignore
from django.db.models import F, Max, Sum
from django.db.models.expressions import Exists, OuterRef
from django.utils.timezone import now
from django_measurement.models import MeasurementField
from django_prices.models import MoneyField, TaxedMoneyField
from measurement.measures import Weight

from ..app.models import App
from ..channel.models import Channel
from ..core.models import ModelWithMetadata
from ..core.permissions import OrderPermissions
from ..core.units import WeightUnits
from ..core.utils.json_serializer import CustomJsonEncoder
from ..core.weight import zero_weight
from ..discount import DiscountValueType
from ..discount.models import Voucher
from ..giftcard.models import GiftCard
from ..payment import ChargeStatus, TransactionKind
from ..payment.model_helpers import get_subtotal, get_total_authorized
from ..payment.models import Payment
from ..shipping.models import ShippingMethod
from . import FulfillmentStatus, OrderEvents, OrderOrigin, OrderStatus


class OrderQueryset(models.QuerySet):
    def get_by_checkout_token(self, token):
        """Return non-draft order with matched checkout token."""
        return self.non_draft().filter(checkout_token=token).first()

    def confirmed(self):
        """Return orders that aren't draft or unconfirmed."""
        return self.exclude(status__in=[OrderStatus.DRAFT, OrderStatus.UNCONFIRMED])

    def non_draft(self):
        """Return orders that aren't draft."""
        return self.exclude(status=OrderStatus.DRAFT)

    def drafts(self):
        """Return draft orders."""
        return self.filter(status=OrderStatus.DRAFT)

    def ready_to_fulfill(self):
        """Return orders that can be fulfilled.

        Orders ready to fulfill are fully paid but unfulfilled (or partially
        fulfilled).
        """
        statuses = {OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED}
        payments = Payment.objects.filter(is_active=True).values("id")
        qs = self.annotate(amount_paid=Sum("payments__captured_amount"))
        return qs.filter(
            Exists(payments.filter(order_id=OuterRef("id"))),
            status__in=statuses,
            total_gross_amount__lte=F("amount_paid"),
        )

    def ready_to_capture(self):
        """Return orders with payments to capture.

        Orders ready to capture are those which are not draft or canceled and
        have a preauthorized payment. The preauthorized payment can not
        already be partially or fully captured.
        """
        payments = Payment.objects.filter(
            is_active=True, charge_status=ChargeStatus.NOT_CHARGED
        ).values("id")
        qs = self.filter(Exists(payments.filter(order_id=OuterRef("id"))))
        return qs.exclude(status={OrderStatus.DRAFT, OrderStatus.CANCELED})

    def ready_to_confirm(self):
        """Return unconfirmed orders."""
        return self.filter(status=OrderStatus.UNCONFIRMED)


class Order(ModelWithMetadata):
    created = models.DateTimeField(default=now, editable=False)
    status = models.CharField(
        max_length=32, default=OrderStatus.UNFULFILLED, choices=OrderStatus.CHOICES
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="orders",
        on_delete=models.SET_NULL,
    )
    language_code = models.CharField(
        max_length=35, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )
    tracking_client_id = models.CharField(max_length=36, blank=True, editable=False)
    billing_address = models.ForeignKey(
        "account.Address",
        related_name="+",
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
    )
    shipping_address = models.ForeignKey(
        "account.Address",
        related_name="+",
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
    )
    user_email = models.EmailField(blank=True, default="")
    original = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    origin = models.CharField(max_length=32, choices=OrderOrigin.CHOICES)

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )

    shipping_method = models.ForeignKey(
        ShippingMethod,
        blank=True,
        null=True,
        related_name="orders",
        on_delete=models.SET_NULL,
    )
    collection_point = models.ForeignKey(
        "warehouse.Warehouse",
        blank=True,
        null=True,
        related_name="orders",
        on_delete=models.SET_NULL,
    )
    shipping_method_name = models.CharField(
        max_length=255, null=True, default=None, blank=True, editable=False
    )
    collection_point_name = models.CharField(
        max_length=255, null=True, default=None, blank=True, editable=False
    )

    channel = models.ForeignKey(
        Channel,
        related_name="orders",
        on_delete=models.PROTECT,
    )
    shipping_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
        editable=False,
    )
    shipping_price_net = MoneyField(
        amount_field="shipping_price_net_amount", currency_field="currency"
    )

    shipping_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
        editable=False,
    )
    shipping_price_gross = MoneyField(
        amount_field="shipping_price_gross_amount", currency_field="currency"
    )

    shipping_price = TaxedMoneyField(
        net_amount_field="shipping_price_net_amount",
        gross_amount_field="shipping_price_gross_amount",
        currency_field="currency",
    )
    shipping_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0.0")
    )

    token = models.CharField(max_length=36, unique=True, blank=True)
    # Token of a checkout instance that this order was created from
    checkout_token = models.CharField(max_length=36, blank=True)

    total_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    undiscounted_total_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    total_net = MoneyField(amount_field="total_net_amount", currency_field="currency")
    undiscounted_total_net = MoneyField(
        amount_field="undiscounted_total_net_amount", currency_field="currency"
    )

    total_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    undiscounted_total_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    total_gross = MoneyField(
        amount_field="total_gross_amount", currency_field="currency"
    )
    undiscounted_total_gross = MoneyField(
        amount_field="undiscounted_total_gross_amount", currency_field="currency"
    )

    total = TaxedMoneyField(
        net_amount_field="total_net_amount",
        gross_amount_field="total_gross_amount",
        currency_field="currency",
    )
    undiscounted_total = TaxedMoneyField(
        net_amount_field="undiscounted_total_net_amount",
        gross_amount_field="undiscounted_total_gross_amount",
        currency_field="currency",
    )

    total_paid_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    total_paid = MoneyField(amount_field="total_paid_amount", currency_field="currency")

    voucher = models.ForeignKey(
        Voucher, blank=True, null=True, related_name="+", on_delete=models.SET_NULL
    )
    gift_cards = models.ManyToManyField(GiftCard, blank=True, related_name="orders")

    display_gross_prices = models.BooleanField(default=True)
    customer_note = models.TextField(blank=True, default="")
    weight = MeasurementField(
        measurement=Weight,
        unit_choices=WeightUnits.CHOICES,  # type: ignore
        default=zero_weight,
    )
    redirect_url = models.URLField(blank=True, null=True)
    search_document = models.TextField(blank=True, default="")

    objects = models.Manager.from_queryset(OrderQueryset)()

    class Meta:
        ordering = ("-pk",)
        permissions = ((OrderPermissions.MANAGE_ORDERS.codename, "Manage orders."),)
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            GinIndex(
                name="order_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["search_document"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="order_email_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["user_email"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        return super().save(*args, **kwargs)

    def is_fully_paid(self):
        return self.total_paid >= self.total.gross

    def is_partly_paid(self):
        return self.total_paid_amount > 0

    def get_customer_email(self):
        return self.user.email if self.user else self.user_email

    def update_total_paid(self):
        self.total_paid_amount = (
            sum(self.payments.values_list("captured_amount", flat=True)) or 0
        )
        self.save(update_fields=["total_paid_amount"])

    def _index_billing_phone(self):
        return self.billing_address.phone

    def _index_shipping_phone(self):
        return self.shipping_address.phone

    def __repr__(self):
        return "<Order #%r>" % (self.id,)

    def __str__(self):
        return "#%d" % (self.id,)

    def get_last_payment(self):
        # Skipping a partial payment is a temporary workaround for storing a basic data
        # about partial payment from Adyen plugin. This is something that will removed
        # in 3.1 by introducing a partial payments feature.
        payments = [payment for payment in self.payments.all() if not payment.partial]
        return max(payments, default=None, key=attrgetter("pk"))

    def is_pre_authorized(self):
        return (
            self.payments.filter(
                is_active=True,
                transactions__kind=TransactionKind.AUTH,
                transactions__action_required=False,
            )
            .filter(transactions__is_success=True)
            .exists()
        )

    def is_captured(self):
        return (
            self.payments.filter(
                is_active=True,
                transactions__kind=TransactionKind.CAPTURE,
                transactions__action_required=False,
            )
            .filter(transactions__is_success=True)
            .exists()
        )

    def is_shipping_required(self):
        return any(line.is_shipping_required for line in self.lines.all())

    def get_subtotal(self):
        return get_subtotal(self.lines.all(), self.currency)

    def get_total_quantity(self):
        return sum([line.quantity for line in self.lines.all()])

    def is_draft(self):
        return self.status == OrderStatus.DRAFT

    def is_unconfirmed(self):
        return self.status == OrderStatus.UNCONFIRMED

    def is_open(self):
        statuses = {OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED}
        return self.status in statuses

    def can_cancel(self):
        statuses_allowed_to_cancel = [
            FulfillmentStatus.CANCELED,
            FulfillmentStatus.REFUNDED,
            FulfillmentStatus.REPLACED,
            FulfillmentStatus.REFUNDED_AND_RETURNED,
            FulfillmentStatus.RETURNED,
        ]
        return (
            not self.fulfillments.exclude(
                status__in=statuses_allowed_to_cancel
            ).exists()
        ) and self.status not in {OrderStatus.CANCELED, OrderStatus.DRAFT}

    def can_capture(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        order_status_ok = self.status not in {OrderStatus.DRAFT, OrderStatus.CANCELED}
        return payment.can_capture() and order_status_ok

    def can_void(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        return payment.can_void()

    def can_refund(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        return payment.can_refund()

    def can_mark_as_paid(self, payments=None):
        if not payments:
            payments = self.payments.all()
        return len(payments) == 0

    @property
    def total_authorized(self):
        return get_total_authorized(self.payments.all(), self.currency)

    @property
    def total_captured(self):
        return self.total_paid

    @property
    def total_balance(self):
        return self.total_captured - self.total.gross

    def get_total_weight(self, *_args):
        return self.weight


class OrderLineQueryset(models.QuerySet):
    def digital(self):
        """Return lines with digital products."""
        for line in self.all():
            if line.is_digital:
                yield line

    def physical(self):
        """Return lines with physical products."""
        for line in self.all():
            if not line.is_digital:
                yield line


class OrderLine(models.Model):
    order = models.ForeignKey(
        Order, related_name="lines", editable=False, on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        "product.ProductVariant",
        related_name="order_lines",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    # max_length is as produced by ProductVariant's display_product method
    product_name = models.CharField(max_length=386)
    variant_name = models.CharField(max_length=255, default="", blank=True)
    translated_product_name = models.CharField(max_length=386, default="", blank=True)
    translated_variant_name = models.CharField(max_length=255, default="", blank=True)
    product_sku = models.CharField(max_length=255, null=True, blank=True)
    # str with GraphQL ID used as fallback when product SKU is not available
    product_variant_id = models.CharField(max_length=255, null=True, blank=True)
    is_shipping_required = models.BooleanField()
    is_gift_card = models.BooleanField()
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_fulfilled = models.IntegerField(
        validators=[MinValueValidator(0)], default=0
    )

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )

    unit_discount_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    unit_discount = MoneyField(
        amount_field="unit_discount_amount", currency_field="currency"
    )
    unit_discount_type = models.CharField(
        max_length=10,
        choices=DiscountValueType.CHOICES,
        default=DiscountValueType.FIXED,
    )
    unit_discount_reason = models.TextField(blank=True, null=True)

    unit_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    # stores the value of the applied discount. Like 20 of %
    unit_discount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    unit_price_net = MoneyField(
        amount_field="unit_price_net_amount", currency_field="currency"
    )

    unit_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    unit_price_gross = MoneyField(
        amount_field="unit_price_gross_amount", currency_field="currency"
    )

    unit_price = TaxedMoneyField(
        net_amount_field="unit_price_net_amount",
        gross_amount_field="unit_price_gross_amount",
        currency="currency",
    )

    total_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    total_price_net = MoneyField(
        amount_field="total_price_net_amount",
        currency_field="currency",
    )

    total_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    total_price_gross = MoneyField(
        amount_field="total_price_gross_amount",
        currency_field="currency",
    )

    total_price = TaxedMoneyField(
        net_amount_field="total_price_net_amount",
        gross_amount_field="total_price_gross_amount",
        currency="currency",
    )

    undiscounted_unit_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    undiscounted_unit_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    undiscounted_unit_price = TaxedMoneyField(
        net_amount_field="undiscounted_unit_price_net_amount",
        gross_amount_field="undiscounted_unit_price_gross_amount",
        currency="currency",
    )

    undiscounted_total_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    undiscounted_total_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    undiscounted_total_price = TaxedMoneyField(
        net_amount_field="undiscounted_total_price_net_amount",
        gross_amount_field="undiscounted_total_price_gross_amount",
        currency="currency",
    )

    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0.0")
    )

    # Fulfilled when voucher code was used for product in the line
    voucher_code = models.CharField(max_length=255, null=True, blank=True)

    # Fulfilled when sale was applied to product in the line
    sale_id = models.CharField(max_length=255, null=True, blank=True)

    objects = models.Manager.from_queryset(OrderLineQueryset)()

    class Meta:
        ordering = ("pk",)

    def __str__(self):
        return (
            f"{self.product_name} ({self.variant_name})"
            if self.variant_name
            else self.product_name
        )

    @property
    def quantity_unfulfilled(self):
        return self.quantity - self.quantity_fulfilled

    @property
    def is_digital(self) -> Optional[bool]:
        """Check if a variant is digital and contains digital content."""
        if not self.variant:
            return None
        is_digital = self.variant.is_digital()
        has_digital = hasattr(self.variant, "digital_content")
        return is_digital and has_digital


class Fulfillment(ModelWithMetadata):
    fulfillment_order = models.PositiveIntegerField(editable=False)
    order = models.ForeignKey(
        Order, related_name="fulfillments", editable=False, on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=32,
        default=FulfillmentStatus.FULFILLED,
        choices=FulfillmentStatus.CHOICES,
    )
    tracking_number = models.CharField(max_length=255, default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)

    shipping_refund_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        null=True,
        blank=True,
    )
    total_refund_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        null=True,
        blank=True,
    )

    class Meta(ModelWithMetadata.Meta):
        ordering = ("pk",)

    def __str__(self):
        return f"Fulfillment #{self.composed_id}"

    def __iter__(self):
        return iter(self.lines.all())

    def save(self, *args, **kwargs):
        """Assign an auto incremented value as a fulfillment order."""
        if not self.pk:
            groups = self.order.fulfillments.all()
            existing_max = groups.aggregate(Max("fulfillment_order"))
            existing_max = existing_max.get("fulfillment_order__max")
            self.fulfillment_order = existing_max + 1 if existing_max is not None else 1
        return super().save(*args, **kwargs)

    @property
    def composed_id(self):
        return "%s-%s" % (self.order.id, self.fulfillment_order)

    def can_edit(self):
        return self.status != FulfillmentStatus.CANCELED

    def get_total_quantity(self):
        return sum([line.quantity for line in self.lines.all()])

    @property
    def is_tracking_number_url(self):
        return bool(match(r"^[-\w]+://", self.tracking_number))


class FulfillmentLine(models.Model):
    order_line = models.ForeignKey(
        OrderLine, related_name="fulfillment_lines", on_delete=models.CASCADE
    )
    fulfillment = models.ForeignKey(
        Fulfillment, related_name="lines", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    stock = models.ForeignKey(
        "warehouse.Stock",
        related_name="fulfillment_lines",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )


class OrderEvent(models.Model):
    """Model used to store events that happened during the order lifecycle.

    Args:
        parameters: Values needed to display the event on the storefront
        type: Type of an order

    """

    date = models.DateTimeField(default=now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=[
            (type_name.upper(), type_name) for type_name, _ in OrderEvents.CHOICES
        ],
    )
    order = models.ForeignKey(Order, related_name="events", on_delete=models.CASCADE)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    app = models.ForeignKey(App, related_name="+", on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ("date",)

    def __repr__(self):
        return f"{self.__class__.__name__}(type={self.type!r}, user={self.user!r})"
