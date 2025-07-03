import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest import mock

import graphene
from prices import Money

from ....checkout import calculations
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import (
    add_variant_to_checkout,
    add_voucher_to_checkout,
    set_external_shipping_id,
)
from ....core.taxes import TaxedMoney
from ....discount import DiscountInfo, VoucherType
from ....plugins.manager import get_plugins_manager
from ....warehouse.models import Stock
from ...tests.utils import get_graphql_content
from .test_checkout import MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE
from .test_checkout_lines import MUTATION_CHECKOUT_LINE_DELETE


def test_checkout_lines_delete_with_not_applicable_voucher(
    user_api_client, checkout_with_item, voucher, channel_USD
):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    voucher.channel_listings.filter(channel=channel_USD).update(
        min_spent_amount=subtotal.gross.amount
    )
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    add_voucher_to_checkout(manager, checkout_info, lines, voucher)
    assert checkout_with_item.voucher_code == voucher.code

    line = checkout_with_item.lines.first()

    line_id = graphene.Node.to_global_id("CheckoutLine", line.pk)
    variables = {"token": checkout_with_item.token, "lineId": line_id}
    response = user_api_client.post_graphql(MUTATION_CHECKOUT_LINE_DELETE, variables)
    content = get_graphql_content(response)

    data = content["data"]["checkoutLineDelete"]
    assert not data["errors"]
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.lines.count() == 0
    assert checkout_with_item.voucher_code is None


def test_checkout_shipping_address_update_with_not_applicable_voucher(
    user_api_client,
    checkout_with_item,
    voucher_shipping_type,
    graphql_address_data,
    address_other_country,
    shipping_method,
):
    assert checkout_with_item.shipping_address is None
    assert checkout_with_item.voucher_code is None

    checkout_with_item.shipping_address = address_other_country
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.save(update_fields=["shipping_address", "shipping_method"])
    assert checkout_with_item.shipping_address.country == address_other_country.country

    voucher = voucher_shipping_type
    assert voucher.countries[0].code == address_other_country.country

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    add_voucher_to_checkout(manager, checkout_info, lines, voucher)
    assert checkout_with_item.voucher_code == voucher.code

    new_address = graphql_address_data
    variables = {"token": checkout_with_item.token, "shippingAddress": new_address}
    response = user_api_client.post_graphql(
        MUTATION_CHECKOUT_SHIPPING_ADDRESS_UPDATE, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkoutShippingAddressUpdate"]
    assert not data["errors"]

    checkout_with_item.refresh_from_db()
    checkout_with_item.shipping_address.refresh_from_db()

    assert checkout_with_item.shipping_address.country == new_address["country"]
    assert checkout_with_item.voucher_code is None


def test_checkout_totals_use_discounts(
    api_client, checkout_with_item, sale, channel_USD
):
    checkout = checkout_with_item
    # make sure that we're testing a variant that is actually on sale
    product = checkout.lines.first().variant.product
    sale.products.add(product)

    query = """
    query getCheckout($token: UUID) {
        checkout(token: $token) {
            lines {
                totalPrice {
                    gross {
                        amount
                    }
                }
            }
            totalPrice {
                gross {
                    amount
                }
            }
            subtotalPrice {
                gross {
                    amount
                }
            }
        }
    }
    """

    variables = {"token": str(checkout.token)}
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkout"]
    sale_channel_listing = sale.channel_listings.get(channel=channel_USD)
    discounts = [
        DiscountInfo(
            sale=sale,
            channel_listings={channel_USD.slug: sale_channel_listing},
            product_ids={product.id},
            category_ids=set(),
            collection_ids=set(),
            variants_ids=set(),
        )
    ]

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
        discounts=discounts,
    )
    assert data["totalPrice"]["gross"]["amount"] == taxed_total.gross.amount
    assert data["subtotalPrice"]["gross"]["amount"] == taxed_total.gross.amount

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    checkout_line_info = lines[0]
    line_total = calculations.checkout_line_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        checkout_line_info=checkout_line_info,
        discounts=discounts,
    ).price_with_sale
    assert data["lines"][0]["totalPrice"]["gross"]["amount"] == line_total.gross.amount


QUERY_GET_CHECKOUT_GIFT_CARD_CODES = """
query getCheckout($token: UUID!) {
  checkout(token: $token) {
    token
    giftCards {
      last4CodeChars
      currentBalance {
        amount
      }
    }
  }
}
"""


def test_checkout_get_gift_card_code(user_api_client, checkout_with_gift_card):
    gift_card = checkout_with_gift_card.gift_cards.first()
    variables = {"token": str(checkout_with_gift_card.token)}
    response = user_api_client.post_graphql(
        QUERY_GET_CHECKOUT_GIFT_CARD_CODES, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["giftCards"][0]
    assert data["last4CodeChars"] == gift_card.display_code
    assert data["currentBalance"]["amount"] == gift_card.current_balance.amount


def test_checkout_get_gift_card_codes(
    user_api_client, checkout_with_gift_card, gift_card_created_by_staff
):
    checkout_with_gift_card.gift_cards.add(gift_card_created_by_staff)
    checkout_with_gift_card.save()
    gift_card_first = checkout_with_gift_card.gift_cards.first()
    gift_card_last = checkout_with_gift_card.gift_cards.last()
    variables = {"token": str(checkout_with_gift_card.token)}
    response = user_api_client.post_graphql(
        QUERY_GET_CHECKOUT_GIFT_CARD_CODES, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["giftCards"]
    assert data[0]["last4CodeChars"] == gift_card_first.display_code
    assert data[0]["currentBalance"]["amount"] == gift_card_first.current_balance.amount
    assert data[1]["last4CodeChars"] == gift_card_last.display_code
    assert data[1]["currentBalance"]["amount"] == gift_card_last.current_balance.amount


def test_checkout_get_gift_card_code_without_gift_card(user_api_client, checkout):
    variables = {"token": str(checkout.token)}
    response = user_api_client.post_graphql(
        QUERY_GET_CHECKOUT_GIFT_CARD_CODES, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["checkout"]["giftCards"]
    assert not data


MUTATION_CHECKOUT_ADD_PROMO_CODE = """
    mutation($token: UUID, $promoCode: String!) {
        checkoutAddPromoCode(
            token: $token, promoCode: $promoCode) {
            errors {
                field
                message
                code
            }
            checkout {
                id
                token
                voucherCode
                giftCards {
                    id
                    last4CodeChars
                }
                totalPrice {
                    gross {
                        amount
                    }
                }
                availableShippingMethods {
                    id
                    price {
                        amount
                    }
                }
                shippingMethod {
                    id
                    price {
                        amount
                    }
                }
            }
        }
    }
"""


def _mutate_checkout_add_promo_code(client, variables):
    response = client.post_graphql(MUTATION_CHECKOUT_ADD_PROMO_CODE, variables)
    content = get_graphql_content(response)
    return content["data"]["checkoutAddPromoCode"]


def test_checkout_add_voucher_code_by_token(api_client, checkout_with_item, voucher):
    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["voucherCode"] == voucher.code


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_checkout_add_voucher_code_by_token_with_external_shipment(
    mock_send_request,
    api_client,
    checkout_with_item,
    voucher,
    shipping_app,
    address,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    mock_send_request.return_value = mock_json_response

    external_shipping_method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    checkout = checkout_with_item
    checkout.shipping_address = address
    set_external_shipping_id(checkout, external_shipping_method_id)
    checkout.save(update_fields=["shipping_address", "private_metadata"])

    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["voucherCode"] == voucher.code
    assert data["checkout"]["shippingMethod"]["id"] == external_shipping_method_id


def test_checkout_add_voucher_code_with_display_gross_prices(
    api_client, checkout_with_item, voucher, site_settings, monkeypatch
):
    site_settings.display_gross_prices = True
    site_settings.save()

    previous_checkout_last_change = checkout_with_item.last_change

    voucher = voucher
    voucher_channel_listing = voucher.channel_listings.first()
    voucher_channel_listing.min_spent_amount = 100
    voucher_channel_listing.save()

    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: TaxedMoney(
            Money(95, "USD"), Money(100, "USD")
        ),
    )

    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["voucherCode"] == voucher.code
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.last_change != previous_checkout_last_change


def test_checkout_add_voucher_code_without_display_gross_prices(
    api_client, checkout_with_item, voucher, site_settings, monkeypatch
):
    site_settings.display_gross_prices = False
    site_settings.save()

    previous_checkout_last_change = checkout_with_item.last_change

    voucher = voucher
    voucher_channel_listing = voucher.channel_listings.first()
    voucher_channel_listing.min_spent_amount = 100
    voucher_channel_listing.save()

    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: TaxedMoney(
            Money(95, "USD"), Money(100, "USD")
        ),
    )

    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"][0]["code"] == CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.name
    assert data["errors"][0]["field"] == "promoCode"

    checkout_with_item.refresh_from_db()
    assert checkout_with_item.last_change == previous_checkout_last_change


def test_checkout_add_voucher_code_variant_unavailable(
    api_client, checkout_with_item, voucher
):
    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    checkout_with_item.lines.first().variant.channel_listings.filter(
        channel=checkout_with_item.channel
    ).delete()
    data = _mutate_checkout_add_promo_code(api_client, variables)

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "lines"


def test_checkout_add_voucher_code_checkout_with_sale(
    api_client, checkout_with_item, voucher_percentage, discount_info
):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    address = checkout_with_item.shipping_address
    subtotal = calculations.checkout_subtotal(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=[discount_info],
    )
    assert subtotal > subtotal_discounted
    previous_checkout_last_change = checkout_with_item.last_change

    variables = {
        "token": checkout_with_item.token,
        "promoCode": voucher_percentage.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    checkout_with_item.refresh_from_db()
    assert not data["errors"]
    assert checkout_with_item.voucher_code == voucher_percentage.code
    assert checkout_with_item.discount_amount == Decimal(1.5)
    assert checkout_with_item.last_change != previous_checkout_last_change


def test_checkout_add_specific_product_voucher_code_checkout_with_sale(
    api_client, checkout_with_item, voucher_specific_product_type, discount_info
):
    voucher = voucher_specific_product_type
    checkout = checkout_with_item
    expected_discount = Decimal(1.5)
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
        discounts=[discount_info],
    )

    assert subtotal > subtotal_discounted
    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    checkout.refresh_from_db()
    assert not data["errors"]
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == expected_discount
    assert checkout.discount == Money(expected_discount, "USD")


def test_checkout_add_products_voucher_code_checkout_with_sale(
    api_client, checkout_with_item, voucher_percentage, discount_info
):
    checkout = checkout_with_item
    product = checkout.lines.first().variant.product
    voucher = voucher_percentage
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher.products.add(product)

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )

    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
        discounts=[discount_info],
    )
    assert subtotal > subtotal_discounted
    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    checkout.refresh_from_db()
    assert not data["errors"]
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == Decimal(1.5)


def test_checkout_add_collection_voucher_code_checkout_with_sale(
    api_client, checkout_with_item, voucher_percentage, discount_info, collection
):
    checkout = checkout_with_item
    voucher = voucher_percentage
    product = checkout.lines.first().variant.product
    product.collections.add(collection)
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher.collections.add(collection)

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
        discounts=[discount_info],
    )
    assert subtotal > subtotal_discounted
    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    checkout.refresh_from_db()
    assert not data["errors"]
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == Decimal(1.5)


def test_checkout_add_category_code_checkout_with_sale(
    api_client, checkout_with_item, voucher_percentage, discount_info
):
    checkout = checkout_with_item
    category = checkout.lines.first().variant.product.category
    voucher = voucher_percentage
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save()
    voucher.categories.add(category)

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    checkout_info = fetch_checkout_info(checkout, lines, [discount_info], manager)
    subtotal_discounted = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
        discounts=[discount_info],
    )
    assert subtotal > subtotal_discounted
    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    checkout.refresh_from_db()
    assert not data["errors"]
    assert checkout.voucher_code == voucher.code
    assert checkout.discount_amount == Decimal(1.5)


def test_checkout_add_voucher_code_not_applicable_voucher(
    api_client, checkout_with_item, voucher_with_high_min_spent_amount
):
    variables = {
        "token": checkout_with_item.token,
        "promoCode": voucher_with_high_min_spent_amount.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_voucher_code_not_assigned_to_channel(
    api_client, checkout_with_item, voucher_without_channel
):
    variables = {
        "token": checkout_with_item.token,
        "promoCode": voucher_without_channel.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_gift_card_code(api_client, checkout_with_item, gift_card):
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"token": checkout_with_item.token, "promoCode": gift_card.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert data["checkout"]["giftCards"][0]["last4CodeChars"] == gift_card.display_code


def test_checkout_add_many_gift_card_code(
    api_client, checkout_with_gift_card, gift_card_created_by_staff
):
    assert checkout_with_gift_card.gift_cards.count() > 0
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_created_by_staff.pk)
    variables = {
        "token": checkout_with_gift_card.token,
        "promoCode": gift_card_created_by_staff.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    gift_card_data = data["checkout"]["giftCards"]
    assert gift_card_id in {gift_card["id"] for gift_card in gift_card_data}


def test_checkout_add_inactive_gift_card_code(
    staff_api_client, checkout_with_item, gift_card
):
    # given
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])

    variables = {"token": checkout_with_item.token, "promoCode": gift_card.code}

    # when
    data = _mutate_checkout_add_promo_code(staff_api_client, variables)

    # then
    assert not data["checkout"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_expired_gift_card_code(
    staff_api_client, checkout_with_item, gift_card
):
    # given
    gift_card.expiry_date = date.today() - timedelta(days=10)
    gift_card.save(update_fields=["expiry_date"])

    variables = {"token": checkout_with_item.token, "promoCode": gift_card.code}

    # when
    data = _mutate_checkout_add_promo_code(staff_api_client, variables)

    # then
    assert not data["checkout"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_used_gift_card_code(
    staff_api_client, checkout_with_item, gift_card_used, customer_user
):
    # given
    checkout_with_item.email = gift_card_used.used_by_email
    checkout_with_item.save(update_fields=["email"])

    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_used.pk)

    variables = {"token": checkout_with_item.token, "promoCode": gift_card_used.code}

    # when
    data = _mutate_checkout_add_promo_code(staff_api_client, variables)

    # then
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert (
        data["checkout"]["giftCards"][0]["last4CodeChars"]
        == gift_card_used.display_code
    )


def test_checkout_add_used_gift_card_code_invalid_user(
    staff_api_client, checkout_with_item, gift_card_used, staff_user
):
    # given
    checkout_with_item.user = staff_user
    assert gift_card_used.used_by_email != checkout_with_item.user.email

    variables = {"token": checkout_with_item.token, "promoCode": gift_card_used.code}

    # when
    data = _mutate_checkout_add_promo_code(staff_api_client, variables)

    # then
    assert not data["checkout"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == CheckoutErrorCode.INVALID.name
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_get_total_with_gift_card(api_client, checkout_with_item, gift_card):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_item.shipping_address,
    )
    total_with_gift_card = taxed_total.gross.amount - gift_card.current_balance_amount

    variables = {"token": checkout_with_item.token, "promoCode": gift_card.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert not data["checkout"]["giftCards"] == []
    assert data["checkout"]["totalPrice"]["gross"]["amount"] == total_with_gift_card


def test_checkout_get_total_with_many_gift_card(
    api_client, checkout_with_gift_card, gift_card_created_by_staff
):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_gift_card)
    checkout_info = fetch_checkout_info(checkout_with_gift_card, lines, [], manager)
    taxed_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout_with_gift_card.shipping_address,
    )
    taxed_total.gross -= checkout_with_gift_card.get_total_gift_cards_balance()
    taxed_total.net -= checkout_with_gift_card.get_total_gift_cards_balance()
    total_with_gift_card = (
        taxed_total.gross.amount - gift_card_created_by_staff.current_balance_amount
    )

    assert checkout_with_gift_card.gift_cards.count() > 0
    variables = {
        "token": checkout_with_gift_card.token,
        "promoCode": gift_card_created_by_staff.code,
    }
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert data["checkout"]["totalPrice"]["gross"]["amount"] == total_with_gift_card


def test_checkout_get_total_with_more_money_on_gift_card(
    api_client, checkout_with_item, gift_card_used, customer_user
):
    checkout_with_item.email = gift_card_used.used_by_email
    checkout_with_item.save(update_fields=["email"])

    variables = {"token": checkout_with_item.token, "promoCode": gift_card_used.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    assert not data["checkout"]["giftCards"] == []
    assert data["checkout"]["totalPrice"]["gross"]["amount"] == 0


def test_checkout_add_same_gift_card_code(api_client, checkout_with_gift_card):
    gift_card = checkout_with_gift_card.gift_cards.first()
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    gift_card_count = checkout_with_gift_card.gift_cards.count()
    variables = {"token": checkout_with_gift_card.token, "promoCode": gift_card.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert data["checkout"]["giftCards"][0]["id"] == gift_card_id
    assert data["checkout"]["giftCards"][0]["last4CodeChars"] == gift_card.display_code
    assert len(data["checkout"]["giftCards"]) == gift_card_count


def test_checkout_add_gift_card_code_in_active_gift_card(
    api_client, checkout_with_item, gift_card
):
    gift_card.is_active = False
    gift_card.save()

    variables = {"token": checkout_with_item.token, "promoCode": gift_card.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_gift_card_code_in_expired_gift_card(
    api_client, checkout_with_item, gift_card
):
    gift_card.expiry_date = date.today() - timedelta(days=1)
    gift_card.save()

    variables = {"token": checkout_with_item.token, "promoCode": gift_card.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_promo_code_invalid_checkout(api_client, voucher):
    variables = {"token": uuid.uuid4(), "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "token"


def test_checkout_add_promo_code_invalid_promo_code(api_client, checkout_with_item):
    variables = {"token": checkout_with_item.token, "promoCode": "unexisting_code"}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "promoCode"


def test_checkout_add_promo_code_invalidate_shipping_method(
    api_client,
    checkout,
    variant_with_many_stocks_different_shipping_zones,
    gift_card_created_by_staff,
    address_usa,
    shipping_method,
    channel_USD,
    voucher,
):
    Stock.objects.update(quantity=5)

    # Free shipping for 50 USD
    shipping_channel_listing = shipping_method.channel_listings.first()
    shipping_channel_listing.minimum_order_price = Money(50, "USD")
    shipping_channel_listing.price = Money(0, "USD")
    shipping_channel_listing.save()

    # Setup checkout with items worth $50
    checkout.shipping_address = address_usa
    checkout.shipping_method = shipping_method
    checkout.billing_address = address_usa
    checkout.save()

    checkout_info = fetch_checkout_info(checkout, [], [], get_plugins_manager())
    variant = variant_with_many_stocks_different_shipping_zones
    add_variant_to_checkout(checkout_info, variant, 5)

    # Apply voucher
    variables = {"token": checkout.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    assert data["checkout"]["shippingMethod"] is None
    assert shipping_method_id not in data["checkout"]["availableShippingMethods"]


def test_checkout_add_promo_code_no_checkout_email(
    api_client, checkout_with_item, voucher
):
    checkout_with_item.email = None
    checkout_with_item.save(update_fields=["email"])

    variables = {"token": checkout_with_item.token, "promoCode": voucher.code}
    data = _mutate_checkout_add_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.EMAIL_NOT_SET.name


MUTATION_CHECKOUT_REMOVE_PROMO_CODE = """
    mutation($token: UUID, $promoCode: String, $promoCodeId: ID) {
        checkoutRemovePromoCode(
            token: $token, promoCode: $promoCode, promoCodeId: $promoCodeId) {
            errors {
                field
                code
                message
            }
            checkout {
                token,
                voucherCode
                giftCards {
                    id
                    last4CodeChars
                }
            }
        }
    }
"""


def _mutate_checkout_remove_promo_code(client, variables):
    response = client.post_graphql(MUTATION_CHECKOUT_REMOVE_PROMO_CODE, variables)
    content = get_graphql_content(response)
    return content["data"]["checkoutRemovePromoCode"]


def test_checkout_remove_voucher_code(api_client, checkout_with_voucher):
    assert checkout_with_voucher.voucher_code is not None
    previous_checkout_last_change = checkout_with_voucher.last_change

    variables = {
        "token": checkout_with_voucher.token,
        "promoCode": checkout_with_voucher.voucher_code,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is None
    assert checkout_with_voucher.voucher_code is None
    assert checkout_with_voucher.last_change != previous_checkout_last_change


def test_checkout_remove_voucher_code_with_inactive_channel(
    api_client, checkout_with_voucher
):
    channel = checkout_with_voucher.channel
    channel.is_active = False
    channel.save()
    previous_checkout_last_change = checkout_with_voucher.last_change

    variables = {
        "token": checkout_with_voucher.token,
        "promoCode": checkout_with_voucher.voucher_code,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] == checkout_with_voucher.voucher_code
    assert checkout_with_voucher.last_change == previous_checkout_last_change


def test_checkout_remove_gift_card_code(api_client, checkout_with_gift_card):
    assert checkout_with_gift_card.gift_cards.count() == 1
    previous_checkout_last_change = checkout_with_gift_card.last_change

    variables = {
        "token": checkout_with_gift_card.token,
        "promoCode": checkout_with_gift_card.gift_cards.first().code,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert data["checkout"]["giftCards"] == []
    assert not checkout_with_gift_card.gift_cards.all().exists()
    checkout_with_gift_card.refresh_from_db()
    assert checkout_with_gift_card.last_change != previous_checkout_last_change


def test_checkout_remove_one_of_gift_cards(
    api_client, checkout_with_gift_card, gift_card_created_by_staff
):
    checkout_with_gift_card.gift_cards.add(gift_card_created_by_staff)
    checkout_with_gift_card.save()
    previous_checkout_last_change = checkout_with_gift_card.last_change
    gift_card_first = checkout_with_gift_card.gift_cards.first()
    gift_card_last = checkout_with_gift_card.gift_cards.last()

    variables = {
        "token": checkout_with_gift_card.token,
        "promoCode": gift_card_first.code,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_gift_cards = checkout_with_gift_card.gift_cards
    assert data["checkout"]["token"] == str(checkout_with_gift_card.token)
    assert checkout_gift_cards.filter(code=gift_card_last.code).exists()
    assert not checkout_gift_cards.filter(code=gift_card_first.code).exists()
    checkout_with_gift_card.refresh_from_db()
    assert checkout_with_gift_card.last_change != previous_checkout_last_change


def test_checkout_remove_promo_code_invalid_promo_code(api_client, checkout_with_item):
    previous_checkout_last_change = checkout_with_item.last_change
    variables = {"token": checkout_with_item.token, "promoCode": "unexisting_code"}

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_item.token)
    checkout_with_item.refresh_from_db()
    assert checkout_with_item.last_change == previous_checkout_last_change


def test_checkout_remove_promo_code_invalid_checkout(api_client, voucher):
    variables = {"token": uuid.uuid4(), "promoCode": voucher.code}

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["field"] == "token"


def test_checkout_remove_voucher_code_by_id(
    api_client, checkout_with_voucher, voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None
    checkout_with_voucher.gift_cards.add(gift_card)

    variables = {
        "token": checkout_with_voucher.token,
        "promoCodeId": graphene.Node.to_global_id("Voucher", voucher.id),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is None
    assert len(data["checkout"]["giftCards"]) == 1
    assert checkout_with_voucher.voucher_code is None


def test_checkout_remove_gift_card_by_id(
    api_client, checkout_with_voucher, gift_card, gift_card_expiry_date
):
    assert checkout_with_voucher.voucher_code is not None
    checkout_with_voucher.gift_cards.add(gift_card, gift_card_expiry_date)

    variables = {
        "token": checkout_with_voucher.token,
        "promoCodeId": graphene.Node.to_global_id("GiftCard", gift_card.id),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    checkout_with_voucher.refresh_from_db()
    assert not data["errors"]
    assert data["checkout"]["token"] == str(checkout_with_voucher.token)
    assert data["checkout"]["voucherCode"] is not None
    gift_cards = data["checkout"]["giftCards"]
    assert len(gift_cards) == 1
    assert gift_cards[0]["id"] == graphene.Node.to_global_id(
        "GiftCard", gift_card_expiry_date.pk
    )


def test_checkout_remove_promo_code_id_and_code_given(
    api_client, checkout_with_voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "token": checkout_with_voucher.token,
        "promoCode": checkout_with_voucher.voucher_code,
        "promoCodeId": graphene.Node.to_global_id("GiftCard", gift_card.id),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_remove_promo_code_no_id_and_code_given(
    api_client, checkout_with_voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "token": checkout_with_voucher.token,
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name


def test_checkout_remove_promo_code_id_does_not_exist(
    api_client, checkout_with_voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "token": checkout_with_voucher.token,
        "promoCodeId": "Abc",
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["field"] == "promoCodeId"


def test_checkout_remove_promo_code_invalid_object_type(
    api_client, checkout_with_voucher, gift_card
):
    assert checkout_with_voucher.voucher_code is not None

    variables = {
        "token": checkout_with_voucher.token,
        "promoCodeId": graphene.Node.to_global_id("Product", gift_card.id),
    }

    data = _mutate_checkout_remove_promo_code(api_client, variables)

    assert data["errors"]
    assert data["errors"][0]["code"] == CheckoutErrorCode.NOT_FOUND.name
    assert data["errors"][0]["field"] == "promoCodeId"
