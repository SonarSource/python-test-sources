from typing import TYPE_CHECKING, Iterable, Optional

from ..core.prices import quantize_price
from ..core.taxes import zero_taxed_money
from ..discount import DiscountInfo
from .interface import CheckoutTaxedPricesData

if TYPE_CHECKING:
    from prices import TaxedMoney

    from ..account.models import Address
    from ..plugins.manager import PluginsManager
    from .fetch import CheckoutInfo, CheckoutLineInfo


def checkout_shipping_price(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return checkout shipping price.

    It takes in account all plugins.
    """
    calculated_checkout_shipping = manager.calculate_checkout_shipping(
        checkout_info, lines, address, discounts or []
    )
    return quantize_price(calculated_checkout_shipping, checkout_info.checkout.currency)


def checkout_subtotal(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total cost of all the checkout lines, taxes included.

    It takes in account all plugins.
    """
    calculated_checkout_subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, address, discounts or []
    )
    return quantize_price(calculated_checkout_subtotal, checkout_info.checkout.currency)


def calculate_checkout_total_with_gift_cards(
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    total = (
        checkout_total(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=address,
            discounts=discounts,
        )
        - checkout_info.checkout.get_total_gift_cards_balance()
    )

    return max(total, zero_taxed_money(total.currency))


def checkout_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    address: Optional["Address"],
    discounts: Optional[Iterable[DiscountInfo]] = None,
) -> "TaxedMoney":
    """Return the total cost of the checkout.

    Total is a cost of all lines and shipping fees, minus checkout discounts,
    taxes included.

    It takes in account all plugins.
    """
    calculated_checkout_total = manager.calculate_checkout_total(
        checkout_info, lines, address, discounts or []
    )
    return quantize_price(calculated_checkout_total, checkout_info.checkout.currency)


def checkout_line_total(
    *,
    manager: "PluginsManager",
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    checkout_line_info: "CheckoutLineInfo",
    discounts: Iterable[DiscountInfo] = [],
) -> "CheckoutTaxedPricesData":
    """Return the total price of provided line, taxes included.

    It takes in account all plugins.
    """
    address = checkout_info.shipping_address or checkout_info.billing_address
    calculated_line_total = manager.calculate_checkout_line_total(
        checkout_info,
        lines,
        checkout_line_info,
        address,
        discounts or [],
    )
    return calculated_line_total
