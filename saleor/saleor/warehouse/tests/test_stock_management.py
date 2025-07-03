from unittest import mock

import pytest
from django.db.models import Sum
from django.db.models.functions import Coalesce

from ...core.exceptions import InsufficientStock
from ...order.fetch import OrderLineInfo
from ...order.models import OrderLine
from ...plugins.manager import get_plugins_manager
from ...tests.utils import flush_post_commit_hooks
from ...warehouse.models import Stock
from ..management import (
    allocate_preorders,
    allocate_stocks,
    deallocate_stock,
    deallocate_stock_for_order,
    decrease_stock,
    increase_allocations,
    increase_stock,
)
from ..models import Allocation, PreorderAllocation

COUNTRY_CODE = "US"


def test_allocate_stocks(order_line, stock, channel_USD):
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    line_data = OrderLineInfo(line=order_line, variant=order_line.variant, quantity=50)

    allocate_stocks(
        [line_data], COUNTRY_CODE, channel_USD.slug, manager=get_plugins_manager()
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    assert stock.quantity == 100
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50


def test_allocate_stocks_multiple_lines(order_line, order, product, stock, channel_USD):
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    variant_2 = product.variants.first()
    stock_2 = Stock.objects.get(product_variant=variant_2)

    order_line_2 = OrderLine.objects.get(pk=order_line.pk)
    order_line_2.pk = None
    order_line_2.product_name = product.name
    order_line_2.variant_name = variant_2.name
    order_line_2.product_sku = variant_2.sku
    order_line_2.variant = variant_2
    order_line_2.save()

    quantity_1 = 50
    quantity_2 = 5
    line_data_1 = OrderLineInfo(
        line=order_line, variant=order_line.variant, quantity=quantity_1
    )
    line_data_2 = OrderLineInfo(
        line=order_line_2, variant=variant_2, quantity=quantity_2
    )

    allocate_stocks(
        [line_data_1, line_data_2],
        COUNTRY_CODE,
        channel_USD.slug,
        manager=get_plugins_manager(),
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == quantity_1

    stock_2.refresh_from_db()
    allocation = Allocation.objects.get(order_line=order_line_2, stock=stock_2)
    assert allocation.quantity_allocated == quantity_2


def test_allocate_stock_many_stocks(order_line, variant_with_many_stocks, channel_USD):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    line_data = OrderLineInfo(line=order_line, variant=order_line.variant, quantity=5)
    allocate_stocks(
        [line_data], COUNTRY_CODE, channel_USD.slug, manager=get_plugins_manager()
    )

    allocations = Allocation.objects.filter(order_line=order_line, stock__in=stocks)
    assert allocations[0].quantity_allocated == 4
    assert allocations[1].quantity_allocated == 1


def test_allocate_stock_with_reservations(
    order_line,
    variant_with_many_stocks,
    channel_USD,
    checkout_line_with_one_reservation,
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    line_data = OrderLineInfo(line=order_line, variant=order_line.variant, quantity=3)
    allocate_stocks(
        [line_data],
        COUNTRY_CODE,
        channel_USD.slug,
        manager=get_plugins_manager(),
        check_reservations=True,
    )

    allocations = Allocation.objects.filter(order_line=order_line, stock__in=stocks)
    assert allocations[0].quantity_allocated == 2
    assert allocations[1].quantity_allocated == 1


def test_allocate_stock_insufficient_stock_due_to_reservations(
    order_line,
    variant_with_many_stocks,
    channel_USD,
    checkout_line_with_reservation_in_many_stocks,
):
    variant = variant_with_many_stocks
    variant.stocks.all()

    line_data = OrderLineInfo(line=order_line, variant=order_line.variant, quantity=5)

    with pytest.raises(InsufficientStock):
        allocate_stocks(
            [line_data],
            COUNTRY_CODE,
            channel_USD.slug,
            manager=get_plugins_manager(),
            check_reservations=True,
        )

    assert not Allocation.objects.exists()


def test_allocate_stock_many_stocks_partially_allocated(
    order_line,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
    channel_USD,
):
    allocated_line = order_line_with_allocation_in_many_stocks
    variant = allocated_line.variant
    stocks = variant.stocks.all()

    line_data = OrderLineInfo(line=order_line, variant=order_line.variant, quantity=3)
    allocate_stocks(
        [line_data], COUNTRY_CODE, channel_USD.slug, manager=get_plugins_manager()
    )

    allocations = Allocation.objects.filter(order_line=order_line, stock__in=stocks)
    assert allocations[0].quantity_allocated == 1
    assert allocations[1].quantity_allocated == 2


def test_allocate_stock_partially_allocated_insufficient_stocks(
    order_line, order_line_with_allocation_in_many_stocks, channel_USD
):
    allocated_line = order_line_with_allocation_in_many_stocks
    variant = allocated_line.variant
    stocks = variant.stocks.all()

    line_data = OrderLineInfo(line=order_line, variant=order_line.variant, quantity=6)
    with pytest.raises(InsufficientStock):
        allocate_stocks(
            [line_data], COUNTRY_CODE, channel_USD.slug, manager=get_plugins_manager()
        )

    assert not Allocation.objects.filter(
        order_line=order_line, stock__in=stocks
    ).exists()


def test_allocate_stocks_no_channel_shipping_zones(order_line, stock, channel_USD):
    channel_USD.shipping_zones.clear()

    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    line_data = OrderLineInfo(line=order_line, variant=order_line.variant, quantity=50)
    with pytest.raises(InsufficientStock):
        allocate_stocks(
            [line_data], COUNTRY_CODE, channel_USD.slug, manager=get_plugins_manager()
        )


def test_allocate_stock_insufficient_stocks(
    order_line, variant_with_many_stocks, channel_USD
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    line_data = OrderLineInfo(line=order_line, variant=order_line.variant, quantity=10)
    with pytest.raises(InsufficientStock):
        allocate_stocks(
            [line_data], COUNTRY_CODE, channel_USD.slug, manager=get_plugins_manager()
        )

    assert not Allocation.objects.filter(
        order_line=order_line, stock__in=stocks
    ).exists()


def test_allocate_stock_insufficient_stocks_for_multiple_lines(
    order_line, variant_with_many_stocks, product, channel_USD
):
    variant = variant_with_many_stocks
    stocks = variant.stocks.all()

    variant_2 = product.variants.first()

    order_line_2 = OrderLine.objects.get(pk=order_line.pk)
    order_line_2.pk = None
    order_line_2.product_name = product.name
    order_line_2.variant_name = variant_2.name
    order_line_2.product_sku = variant_2.sku
    order_line_2.variant = variant_2
    order_line_2.save()

    quantity_1 = 100
    quantity_2 = 100
    line_data_1 = OrderLineInfo(
        line=order_line, variant=order_line.variant, quantity=quantity_1
    )
    line_data_2 = OrderLineInfo(
        line=order_line_2, variant=variant_2, quantity=quantity_2
    )

    with pytest.raises(InsufficientStock) as exc:
        allocate_stocks(
            [line_data_1, line_data_2],
            COUNTRY_CODE,
            channel_USD.slug,
            manager=get_plugins_manager(),
        )

    assert set(item.variant for item in exc._excinfo[1].items) == {variant, variant_2}

    assert not Allocation.objects.filter(
        order_line=order_line, stock__in=stocks
    ).exists()


def test_deallocate_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    deallocate_stock(
        [
            OrderLineInfo(
                line=allocation.order_line, quantity=80, variant=stock.product_variant
            )
        ],
        manager=get_plugins_manager(),
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 0


def test_deallocate_stock_when_quantity_less_than_zero(allocation):
    stock = allocation.stock
    stock.quantity = -10
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    deallocate_stock(
        [
            OrderLineInfo(
                line=allocation.order_line, quantity=80, variant=stock.product_variant
            )
        ],
        manager=get_plugins_manager(),
    )

    stock.refresh_from_db()
    assert stock.quantity == -10
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 0


def test_deallocate_stock_partially(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    deallocate_stock(
        [
            OrderLineInfo(
                line=allocation.order_line, quantity=50, variant=stock.product_variant
            )
        ],
        manager=get_plugins_manager(),
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 30


def test_deallocate_stock_many_allocations(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks

    deallocate_stock(
        [OrderLineInfo(line=order_line, quantity=3, variant=order_line.variant)],
        manager=get_plugins_manager(),
    )

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0


def test_deallocate_stock_many_allocations_partially(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks

    deallocate_stock(
        [OrderLineInfo(line=order_line, quantity=1, variant=order_line.variant)],
        manager=get_plugins_manager(),
    )

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 1
    assert allocations[1].quantity_allocated == 1


def test_increase_stock_without_allocate(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    increase_stock(allocation.order_line, stock.warehouse, 50, allocate=False)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 80


def test_increase_stock_with_allocate(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])

    increase_stock(allocation.order_line, stock.warehouse, 50, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 130


def test_increase_stock_with_new_allocation(order_line, stock):
    assert not Allocation.objects.filter(order_line=order_line, stock=stock).exists()
    stock.quantity = 100
    stock.save(update_fields=["quantity"])

    increase_stock(order_line, stock.warehouse, 50, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 150
    allocation = Allocation.objects.get(order_line=order_line, stock=stock)
    assert allocation.quantity_allocated == 50


@pytest.mark.parametrize("quantity", (19, 20))
def test_increase_allocations(quantity, allocation):
    order_line = allocation.order_line
    order_line_info = OrderLineInfo(
        line=order_line,
        quantity=quantity,
        variant=order_line.variant,
        warehouse_pk=allocation.stock.warehouse.pk,
    )
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    initially_allocated = 80
    allocation.quantity_allocated = initially_allocated
    allocation.save(update_fields=["quantity_allocated"])

    increase_allocations(
        [order_line_info], order_line.order.channel.slug, manager=get_plugins_manager()
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    assert (
        order_line.allocations.all().aggregate(Sum("quantity_allocated"))[
            "quantity_allocated__sum"
        ]
        == initially_allocated + quantity
    )


def test_increase_allocation_insufficient_stock(allocation):
    order_line = allocation.order_line
    order_line_info = OrderLineInfo(
        line=order_line,
        quantity=21,
        variant=order_line.variant,
        warehouse_pk=allocation.stock.warehouse.pk,
    )
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    initially_allocated = 80
    allocation.quantity_allocated = initially_allocated
    allocation.save(update_fields=["quantity_allocated"])

    with pytest.raises(InsufficientStock):
        increase_allocations(
            [order_line_info],
            order_line.order.channel.slug,
            manager=get_plugins_manager(),
        )

    stock.refresh_from_db()
    assert stock.quantity == 100
    assert (
        order_line.allocations.all().aggregate(Sum("quantity_allocated"))[
            "quantity_allocated__sum"
        ]
        == initially_allocated
    )


@mock.patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_increase_stock_with_back_in_stock_webhook_triggered_without_allocation(
    product_variant_back_in_stock_webhook, allocation
):
    stock = allocation.stock
    stock.quantity = 0
    stock.save(update_fields=["quantity"])

    increase_stock(allocation.order_line, stock.warehouse, 50, allocate=False)
    flush_post_commit_hooks()

    stock.refresh_from_db()
    assert stock.quantity == 50
    product_variant_back_in_stock_webhook.assert_not_called()


def test_decrease_stock(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineInfo(
                line=allocation.order_line,
                quantity=50,
                variant=stock.product_variant,
                warehouse_pk=warehouse_pk,
            )
        ],
        manager=get_plugins_manager(),
    )

    stock.refresh_from_db()
    assert stock.quantity == 50
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 30


@pytest.mark.parametrize("quantity, expected_allocated", ((50, 30), (200, 0)))
def test_decrease_stock_without_stock_update(quantity, expected_allocated, allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineInfo(
                line=allocation.order_line,
                quantity=quantity,
                variant=stock.product_variant,
                warehouse_pk=warehouse_pk,
            )
        ],
        manager=get_plugins_manager(),
        update_stocks=False,
    )

    stock.refresh_from_db()
    assert stock.quantity == 100
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == expected_allocated


def test_decrease_stock_multiple_lines(allocations):
    allocation_1 = allocations[0]
    allocation_2 = allocations[0]

    stock = allocation_1.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation_1.quantity_allocated = 80
    allocation_1.save(update_fields=["quantity_allocated"])
    warehouse_pk_1 = allocation_1.stock.warehouse.pk

    allocation_2.quantity_allocated = 80
    allocation_2.save(update_fields=["quantity_allocated"])
    warehouse_pk_2 = allocation_2.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineInfo(
                line=allocation_1.order_line,
                quantity=50,
                variant=allocation_1.order_line.variant,
                warehouse_pk=warehouse_pk_1,
            ),
            OrderLineInfo(
                line=allocation_2.order_line,
                quantity=20,
                variant=allocation_2.order_line.variant,
                warehouse_pk=warehouse_pk_2,
            ),
        ],
        manager=get_plugins_manager(),
    )

    stock.refresh_from_db()
    assert stock.quantity == 30
    allocation_1.refresh_from_db()
    assert allocation_1.quantity_allocated == 10


def test_decrease_stock_multiple_lines_deallocate_stock_raises_error(order_with_lines):
    """Ensure that when some of the lines raise an error during the deallocation
    quantity allocated value for all allocation will be updated."""

    # given
    order_line_1 = order_with_lines.lines.first()
    order_line_2 = order_with_lines.lines.last()

    allocation_1 = order_line_1.allocations.first()
    allocation_2 = order_line_2.allocations.first()

    stock_quantity = 100
    allocation_1_qty_allocated = 10
    allocation_2_qty_allocated = 80

    stock_1 = allocation_1.stock
    stock_2 = allocation_2.stock
    stock_1.quantity = stock_quantity
    stock_2.quantity = stock_quantity
    Stock.objects.bulk_update([stock_1, stock_2], ["quantity"])

    allocation_1.quantity_allocated = allocation_1_qty_allocated
    allocation_1.order_line = order_line_1
    warehouse_pk_1 = stock_1.warehouse.pk

    allocation_2.quantity_allocated = allocation_2_qty_allocated
    allocation_2.order_line = order_line_2
    warehouse_pk_2 = stock_2.warehouse.pk

    Allocation.objects.bulk_update(
        [allocation_1, allocation_2], ["quantity_allocated", "order_line"]
    )

    line_1_qty = 50
    line_2_qty = 20

    # when
    decrease_stock(
        [
            OrderLineInfo(
                line=order_line_1,
                quantity=line_1_qty,
                variant=order_line_1.variant,
                warehouse_pk=warehouse_pk_1,
            ),
            OrderLineInfo(
                line=order_line_2,
                quantity=line_2_qty,
                variant=order_line_2.variant,
                warehouse_pk=warehouse_pk_2,
            ),
        ],
        manager=get_plugins_manager(),
    )

    # then
    stock_1.refresh_from_db()
    assert stock_1.quantity == stock_quantity - line_1_qty

    stock_2.refresh_from_db()
    assert stock_2.quantity == stock_quantity - line_2_qty

    allocation_1.refresh_from_db()
    assert allocation_1.quantity_allocated == 0

    allocation_2.refresh_from_db()
    assert allocation_2.quantity_allocated == allocation_2_qty_allocated - line_2_qty


def test_decrease_stock_partially(allocation):
    stock = allocation.stock
    stock.quantity = 100
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineInfo(
                line=allocation.order_line,
                quantity=80,
                variant=stock.product_variant,
                warehouse_pk=str(warehouse_pk),
            )
        ],
        manager=get_plugins_manager(),
    )

    stock.refresh_from_db()
    assert stock.quantity == 20
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 0


def test_decrease_stock_many_allocations(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[1].stock.warehouse.pk

    decrease_stock(
        [
            OrderLineInfo(
                line=order_line,
                quantity=3,
                variant=order_line.variant,
                warehouse_pk=str(warehouse_pk),
            )
        ],
        manager=get_plugins_manager(),
    )

    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0
    assert allocations[0].stock.quantity == 4
    assert allocations[1].stock.quantity == 0


def test_decrease_stock_many_allocations_partially(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[0].stock.warehouse.pk

    decrease_stock(
        [
            OrderLineInfo(
                line=order_line,
                quantity=2,
                variant=order_line.variant,
                warehouse_pk=str(warehouse_pk),
            )
        ],
        manager=get_plugins_manager(),
    ),

    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 1
    assert allocations[0].stock.quantity == 2
    assert allocations[1].stock.quantity == 3


def test_decrease_stock_more_then_allocated(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    allocations = order_line.allocations.all()
    warehouse_pk = allocations[0].stock.warehouse.pk
    quantity_allocated = allocations.aggregate(
        quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
    )["quantity_allocated"]
    assert quantity_allocated < 4

    decrease_stock(
        [
            OrderLineInfo(
                line=order_line,
                quantity=4,
                variant=order_line.variant,
                warehouse_pk=warehouse_pk,
            )
        ],
        manager=get_plugins_manager(),
    )

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0
    assert allocations[0].stock.quantity == 0
    assert allocations[1].stock.quantity == 3


def test_decrease_stock_insufficient_stock(allocation):
    stock = allocation.stock
    stock.quantity = 20
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 80
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    with pytest.raises(InsufficientStock):
        decrease_stock(
            [
                OrderLineInfo(
                    line=allocation.order_line,
                    quantity=50,
                    variant=stock.product_variant,
                    warehouse_pk=warehouse_pk,
                )
            ],
            manager=get_plugins_manager(),
        )

    stock.refresh_from_db()
    assert stock.quantity == 20
    allocation.refresh_from_db()
    assert allocation.quantity_allocated == 80


def test_deallocate_stock_for_order(
    order_line_with_allocation_in_many_stocks,
):
    order_line = order_line_with_allocation_in_many_stocks
    order = order_line.order

    deallocate_stock_for_order(order, manager=get_plugins_manager())

    allocations = order_line.allocations.all()
    assert allocations[0].quantity_allocated == 0
    assert allocations[1].quantity_allocated == 0


@mock.patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_increase_stock_with_back_in_stock_webhook_not_triggered(
    product_variant_back_in_stock_webhook, allocation
):
    stock = allocation.stock
    stock.quantity = 10
    stock.save(update_fields=["quantity"])

    increase_stock(allocation.order_line, stock.warehouse, 50, allocate=False)

    stock.refresh_from_db()
    assert stock.quantity == 60

    flush_post_commit_hooks()
    product_variant_back_in_stock_webhook.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.product_variant_back_in_stock")
def test_increase_stock_with_back_in_stock_webhook_not_triggered_with_allocation(
    product_variant_back_in_stock_webhook, allocation
):
    stock = allocation.stock
    stock.quantity = 0
    stock.save(update_fields=["quantity"])

    increase_stock(allocation.order_line, stock.warehouse, 30, allocate=True)

    stock.refresh_from_db()
    assert stock.quantity == 30

    flush_post_commit_hooks()
    product_variant_back_in_stock_webhook.assert_not_called()


@mock.patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_decrease_stock_with_out_of_stock_webhook_triggered(
    product_variant_out_of_stock_webhook_mock, allocation
):
    stock = allocation.stock
    stock.quantity = 50
    stock.save(update_fields=["quantity"])
    allocation.quantity_allocated = 50
    allocation.save(update_fields=["quantity_allocated"])
    warehouse_pk = allocation.stock.warehouse.pk

    decrease_stock(
        [
            OrderLineInfo(
                line=allocation.order_line,
                quantity=50,
                variant=stock.product_variant,
                warehouse_pk=warehouse_pk,
            )
        ],
        manager=get_plugins_manager(),
    )

    flush_post_commit_hooks()

    product_variant_out_of_stock_webhook_mock.assert_called_once()


def test_allocate_preorders(
    order_line, preorder_variant_channel_threshold, channel_USD
):
    variant = preorder_variant_channel_threshold
    channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    channel_listing.preorder_quantity_threshold = 100
    channel_listing.save(update_fields=["preorder_quantity_threshold"])

    line_data = OrderLineInfo(line=order_line, variant=variant, quantity=50)

    allocate_preorders([line_data], channel_USD.slug)

    channel_listing.refresh_from_db()
    assert channel_listing.preorder_quantity_threshold == 100
    allocation = PreorderAllocation.objects.get(
        order_line=order_line,
        product_variant_channel_listing=channel_listing,
    )
    assert allocation.quantity == 50


def test_allocate_preorders_with_allocation(
    order_line,
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
    channel_USD,
):
    variant = preorder_variant_global_and_channel_threshold
    channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    channel_listing.preorder_quantity_threshold = 10
    channel_listing.save(update_fields=["preorder_quantity_threshold"])

    quantity_to_allocate = 2
    line_data = OrderLineInfo(
        line=order_line, variant=variant, quantity=quantity_to_allocate
    )

    allocate_preorders([line_data], channel_USD.slug)

    channel_listing.refresh_from_db()
    assert channel_listing.preorder_quantity_threshold == 10
    allocation = PreorderAllocation.objects.get(
        order_line=order_line,
        product_variant_channel_listing=channel_listing,
    )
    assert allocation.quantity == quantity_to_allocate


def test_allocate_preorders_insufficient_stocks_channel_threshold(
    order_line, preorder_variant_channel_threshold, channel_USD
):
    variant = preorder_variant_channel_threshold
    channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    channel_listings = variant.channel_listings.all()

    line_data = OrderLineInfo(
        line=order_line,
        variant=variant,
        quantity=channel_listing.preorder_quantity_threshold + 1,
    )
    with pytest.raises(InsufficientStock):
        allocate_preorders([line_data], channel_USD.slug)

    assert not PreorderAllocation.objects.filter(
        order_line=order_line,
        product_variant_channel_listing__in=channel_listings,
    ).exists()


def test_allocate_preorders_insufficient_stocks_global_threshold(
    order_line, preorder_variant_global_threshold, channel_USD
):
    variant = preorder_variant_global_threshold
    channel_listings = variant.channel_listings.all()
    global_allocation = sum(
        channel_listings.annotate(
            allocated_preorder_quantity=Coalesce(
                Sum("preorder_allocations__quantity"), 0
            )
        ).values_list("allocated_preorder_quantity", flat=True)
    )
    available_preorder_quantity = variant.preorder_global_threshold - global_allocation

    line_data = OrderLineInfo(
        line=order_line,
        variant=variant,
        quantity=available_preorder_quantity + 1,
    )
    with pytest.raises(InsufficientStock):
        allocate_preorders([line_data], channel_USD.slug)

    assert not PreorderAllocation.objects.filter(
        order_line=order_line,
        product_variant_channel_listing__in=channel_listings,
    ).exists()


def test_allocate_preorders_with_channel_reservations(
    order_line, checkout_line_with_reserved_preorder_item, channel_USD
):
    variant = checkout_line_with_reserved_preorder_item.variant
    channel_listing = variant.channel_listings.get(channel_id=channel_USD.id)
    channel_listing.preorder_quantity_threshold = 5
    channel_listing.save(update_fields=["preorder_quantity_threshold"])

    line_data = OrderLineInfo(line=order_line, variant=variant, quantity=5)

    with pytest.raises(InsufficientStock):
        allocate_preorders(
            [line_data],
            channel_USD.slug,
            check_reservations=True,
            checkout_lines=[],
        )

    # Allocation passes when checkout line is passed
    allocate_preorders(
        [line_data],
        channel_USD.slug,
        check_reservations=True,
        checkout_lines=[checkout_line_with_reserved_preorder_item],
    )


def test_allocate_preorders_with_global_reservations(
    order_line, checkout_line_with_reserved_preorder_item, channel_USD
):
    variant = checkout_line_with_reserved_preorder_item.variant
    variant.preorder_global_threshold = 5
    variant.save()

    line_data = OrderLineInfo(line=order_line, variant=variant, quantity=5)

    with pytest.raises(InsufficientStock):
        allocate_preorders(
            [line_data],
            channel_USD.slug,
            check_reservations=True,
            checkout_lines=[],
        )

    # Allocation passes when checkout line is passed
    allocate_preorders(
        [line_data],
        channel_USD.slug,
        check_reservations=True,
        checkout_lines=[checkout_line_with_reserved_preorder_item],
    )
