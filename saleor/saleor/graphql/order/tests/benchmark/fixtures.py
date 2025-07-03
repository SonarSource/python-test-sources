import random
import uuid
from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from .....account.models import User
from .....order import OrderEvents, OrderStatus
from .....order.models import Fulfillment, Order, OrderEvent, OrderLine
from .....payment import ChargeStatus
from .....payment.models import Payment

ORDER_COUNT_IN_BENCHMARKS = 10
EVENTS_PER_ORDER = 5
LINES_PER_ORDER = 3


def _prepare_payments_for_order(order):
    return [
        Payment(
            gateway="mirumee.payments.dummy",
            order=order,
            is_active=True,
            charge_status=ChargeStatus.NOT_CHARGED,
        ),
        Payment(
            gateway="mirumee.payments.dummy",
            order=order,
            is_active=True,
            charge_status=ChargeStatus.PARTIALLY_CHARGED,
            captured_amount=Decimal("6.0"),
        ),
        Payment(
            gateway="mirumee.payments.dummy",
            order=order,
            is_active=True,
            charge_status=ChargeStatus.FULLY_CHARGED,
            captured_amount=Decimal("10.0"),
        ),
    ]


def _prepare_events_for_order(order):
    return [
        OrderEvent(order=order, type=random.choice(OrderEvents.CHOICES)[0])
        for _ in range(EVENTS_PER_ORDER)
    ]


def _prepare_lines_for_order(order, variant_with_image):
    price = TaxedMoney(
        net=Money(amount=5, currency="USD"), gross=Money(amount=5, currency="USD")
    )
    return [
        OrderLine(
            order=order,
            variant=variant_with_image,
            quantity=5,
            is_shipping_required=True,
            is_gift_card=False,
            unit_price=price,
            total_price=price,
        )
        for _ in range(LINES_PER_ORDER)
    ]


@pytest.fixture
def users_for_order_benchmarks(address):
    users = [
        User(
            email=f"john.doe.{i}@example.com",
            is_active=True,
            default_billing_address=address.get_copy(),
            default_shipping_address=address.get_copy(),
            first_name=f"John_{i}",
            last_name=f"Doe_{i}",
        )
        for i in range(ORDER_COUNT_IN_BENCHMARKS)
    ]
    return User.objects.bulk_create(users)


@pytest.fixture
def orders_for_benchmarks(
    channel_USD,
    address,
    payment_dummy,
    users_for_order_benchmarks,
    variant_with_image,
    shipping_method,
):
    orders = [
        Order(
            token=str(uuid.uuid4()),
            channel=channel_USD,
            billing_address=address.get_copy(),
            shipping_address=address.get_copy(),
            shipping_method=shipping_method,
            user=users_for_order_benchmarks[i],
            total=TaxedMoney(net=Money(i, "USD"), gross=Money(i, "USD")),
        )
        for i in range(ORDER_COUNT_IN_BENCHMARKS)
    ]
    created_orders = Order.objects.bulk_create(orders)

    payments = []
    events = []
    fulfillments = []
    lines = []

    for order in created_orders:
        new_payments = _prepare_payments_for_order(order)
        new_events = _prepare_events_for_order(order)
        new_lines = _prepare_lines_for_order(order, variant_with_image)
        payments.extend(new_payments)
        events.extend(new_events)
        lines.extend(new_lines)
        fulfillments.append(Fulfillment(order=order, fulfillment_order=order.id))

    Payment.objects.bulk_create(payments)
    OrderEvent.objects.bulk_create(events)
    Fulfillment.objects.bulk_create(fulfillments)
    OrderLine.objects.bulk_create(lines)

    return created_orders


@pytest.fixture
def draft_orders_for_benchmarks(orders_for_benchmarks):
    for order in orders_for_benchmarks:
        order.status = OrderStatus.DRAFT

    Order.objects.bulk_update(orders_for_benchmarks, ["status"])

    return orders_for_benchmarks
