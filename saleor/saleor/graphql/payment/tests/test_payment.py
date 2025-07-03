import json
from decimal import Decimal
from unittest.mock import ANY, Mock, patch

import graphene
import pytest

from ....checkout import calculations
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import add_variant_to_checkout
from ....payment import PaymentError
from ....payment.error_codes import PaymentErrorCode
from ....payment.gateways.dummy_credit_card import (
    TOKEN_EXPIRED,
    TOKEN_VALIDATION_MAPPING,
)
from ....payment.interface import (
    CustomerSource,
    InitializedPaymentResponse,
    PaymentMethodInfo,
    StorePaymentMethodEnum,
    TokenConfig,
)
from ....payment.models import ChargeStatus, Payment, TransactionKind
from ....payment.utils import fetch_customer_id, store_customer_id
from ....plugins.manager import PluginsManager, get_plugins_manager
from ...tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ..enums import OrderAction, PaymentChargeStatusEnum
from ..mutations import PaymentCheckBalance

DUMMY_GATEWAY = "mirumee.payments.dummy"

VOID_QUERY = """
    mutation PaymentVoid($paymentId: ID!) {
        paymentVoid(paymentId: $paymentId) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_payment_void_success(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.is_active is False
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID


def test_payment_void_gateway_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert data["errors"]
    assert data["errors"][0]["field"] is None
    assert data["errors"][0]["message"] == "Unable to void the transaction."
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    assert payment_txn_preauth.is_active is True
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID
    assert not txn.is_success


CREATE_PAYMENT_MUTATION = """
    mutation CheckoutPaymentCreate(
        $token: UUID,
        $input: PaymentInput!,
    ) {
        checkoutPaymentCreate(
            token: $token,
            input: $input,
        ) {
            payment {
                chargeStatus
            }
            errors {
                code
                field
                variants
            }
        }
    }
    """


def test_checkout_add_payment_without_shipping_method_and_not_shipping_required(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert not data["errors"]
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name


def test_checkout_add_payment_without_shipping_method_with_shipping_required(
    user_api_client, checkout_with_shipping_required, address
):
    checkout = checkout_with_shipping_required

    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert data["errors"][0]["code"] == "SHIPPING_METHOD_NOT_SET"
    assert data["errors"][0]["field"] == "shippingMethod"


def test_checkout_add_payment_with_shipping_method_and_shipping_required(
    user_api_client, checkout_with_shipping_required, other_shipping_method, address
):
    checkout = checkout_with_shipping_required
    checkout.billing_address = address
    checkout.shipping_address = address
    checkout.shipping_method = other_shipping_method
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["errors"]
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name


def test_checkout_add_payment(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.email = "old@example"
    checkout.user = customer_user
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["errors"]
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name
    assert payment.return_url == return_url
    assert payment.billing_email == customer_user.email


def test_checkout_add_payment_default_amount(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    variables = {
        "token": checkout.token,
        "input": {"gateway": DUMMY_GATEWAY, "token": "sample-token"},
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert not data["errors"]
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


def test_checkout_add_payment_bad_amount(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )

    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": str(total.gross.amount + Decimal(1)),
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert (
        data["errors"][0]["code"] == PaymentErrorCode.PARTIAL_PAYMENT_NOT_ALLOWED.name
    )


def test_checkout_add_payment_no_checkout_email(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    checkout = checkout_without_shipping_required
    checkout.email = None
    checkout.save(update_fields=["email"])

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == PaymentErrorCode.CHECKOUT_EMAIL_NOT_SET.name


def test_checkout_add_payment_not_supported_gateways(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.currency = "EUR"
    checkout.save(update_fields=["billing_address", "currency"])

    variables = {
        "token": checkout.token,
        "input": {"gateway": DUMMY_GATEWAY, "token": "sample-token", "amount": "10.0"},
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert data["errors"][0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.name
    assert data["errors"][0]["field"] == "gateway"


def test_use_checkout_billing_address_as_payment_billing(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    # check if proper error is returned if address is missing
    assert data["errors"][0]["field"] == "billingAddress"
    assert data["errors"][0]["code"] == PaymentErrorCode.BILLING_ADDRESS_NOT_SET.name

    # assign the address and try again
    address.street_address_1 = "spanish-inqusition"
    address.save()
    checkout.billing_address = address
    checkout.save()
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    get_graphql_content(response)

    checkout.refresh_from_db()
    assert checkout.payments.count() == 1
    payment = checkout.payments.first()
    assert payment.billing_address_1 == address.street_address_1


def test_create_payment_for_checkout_with_active_payments(
    checkout_with_payments, user_api_client, address, product_without_shipping
):
    # given
    checkout = checkout_with_payments
    address.street_address_1 = "spanish-inqusition"
    address.save()
    checkout.billing_address = address
    manager = get_plugins_manager()
    variant = product_without_shipping.variants.get()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    add_variant_to_checkout(checkout_info, variant, 1)
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }

    payments_count = checkout.payments.count()
    previous_active_payments = checkout.payments.filter(is_active=True)
    previous_active_payments_ids = list(
        previous_active_payments.values_list("pk", flat=True)
    )
    assert len(previous_active_payments_ids) > 0

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["errors"]
    checkout.refresh_from_db()
    assert checkout.payments.all().count() == payments_count + 1
    active_payments = checkout.payments.all().filter(is_active=True)
    assert active_payments.count() == 1
    assert active_payments.first().pk not in previous_active_payments_ids


@pytest.mark.parametrize(
    "store",
    [
        StorePaymentMethodEnum.NONE,
        StorePaymentMethodEnum.ON_SESSION,
        StorePaymentMethodEnum.OFF_SESSION,
    ],
)
def test_create_payment_with_store(
    user_api_client, checkout_without_shipping_required, address, store
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "storePaymentMethod": store,
        },
    }

    # when
    user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    checkout.refresh_from_db()
    payment = checkout.payments.first()
    assert payment.store_payment_method == store.lower()


@pytest.mark.parametrize(
    "metadata", [[{"key": f"key{i}", "value": f"value{i}"} for i in range(5)], [], None]
)
def test_create_payment_with_metadata(
    user_api_client, checkout_without_shipping_required, address, metadata
):
    # given
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "metadata": metadata,
        },
    }

    # when
    user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)

    # then
    checkout.refresh_from_db()
    payment = checkout.payments.first()
    assert payment.metadata == {m["key"]: m["value"] for m in metadata or {}}


def test_checkout_add_payment_no_variant_channel_listings(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.email = "old@example"
    checkout.user = customer_user
    checkout.save()

    variant = checkout.lines.first().variant
    variant.product.channel_listings.filter(channel=checkout.channel_id).delete()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "token"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
    ]


def test_checkout_add_payment_no_product_channel_listings(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.email = "old@example"
    checkout.user = customer_user
    checkout.save()

    variant = checkout.lines.first().variant
    variant.channel_listings.filter(channel=checkout.channel_id).delete()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.name
    assert errors[0]["field"] == "token"
    assert errors[0]["variants"] == [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
    ]


def test_checkout_add_payment_checkout_without_lines(
    user_api_client, checkout_without_shipping_required, address, customer_user
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.email = "old@example"
    checkout.user = customer_user
    checkout.save()

    checkout.lines.all().delete()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager, checkout_info=checkout_info, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "token": checkout.token,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "lines"
    assert errors[0]["code"] == PaymentErrorCode.NO_CHECKOUT_LINES.name


CAPTURE_QUERY = """
    mutation PaymentCapture($paymentId: ID!, $amount: PositiveDecimal!) {
        paymentCapture(paymentId: $paymentId, amount: $amount) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_payment_capture_success(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE


def test_payment_capture_with_invalid_argument(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Amount should be a positive number."


def test_payment_capture_with_payment_non_authorized_yet(
    staff_api_client, permission_manage_orders, payment_dummy
):
    """Ensure capture a payment that is set as authorized is failing with
    the proper error message.
    """
    payment = payment_dummy
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 1}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [
        {"field": None, "message": "Cannot find successful auth transaction."}
    ]


def test_payment_capture_gateway_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    payment = payment_txn_preauth

    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [{"field": None, "message": "Unable to process capture"}]

    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.is_success


@patch(
    "saleor.payment.gateways.dummy_credit_card.plugin."
    "DummyCreditCardGatewayPlugin.DEFAULT_ACTIVE",
    True,
)
def test_payment_capture_gateway_dummy_credit_card_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    token = TOKEN_EXPIRED
    error = TOKEN_VALIDATION_MAPPING[token]

    payment = payment_txn_preauth
    payment.gateway = "mirumee.payments.dummy_credit_card"
    payment.save()

    transaction = payment.transactions.last()
    transaction.token = token
    transaction.save()

    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [{"field": None, "message": error}]

    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.is_success


REFUND_QUERY = """
    mutation PaymentRefund($paymentId: ID!, $amount: PositiveDecimal!) {
        paymentRefund(paymentId: $paymentId, amount: $amount) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_payment_refund_success(
    staff_api_client, permission_manage_orders, payment_txn_captured
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment.total)}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert not data["errors"]
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND


def test_payment_refund_with_invalid_argument(
    staff_api_client, permission_manage_orders, payment_txn_captured
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Amount should be a positive number."


def test_payment_refund_error(
    staff_api_client, permission_manage_orders, payment_txn_captured, monkeypatch
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]

    assert data["errors"] == [{"field": None, "message": "Unable to process refund"}]
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success


PAYMENT_QUERY = """ query Payments($filter: PaymentFilterInput){
    payments(first: 20, filter: $filter) {
        edges {
            node {
                id
                gateway
                capturedAmount {
                    amount
                    currency
                }
                total {
                    amount
                    currency
                }
                actions
                chargeStatus
                transactions {
                    error
                    gatewayResponse
                    amount {
                        currency
                        amount
                    }
                }
            }
        }
    }
}
"""


def test_payments_query(
    payment_txn_captured, permission_manage_orders, staff_api_client
):
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["payments"]["edges"][0]["node"]
    pay = payment_txn_captured
    assert data["gateway"] == pay.gateway
    amount = str(data["capturedAmount"]["amount"])
    assert Decimal(amount) == pay.captured_amount
    assert data["capturedAmount"]["currency"] == pay.currency
    total = str(data["total"]["amount"])
    assert Decimal(total) == pay.total
    assert data["total"]["currency"] == pay.currency
    assert data["chargeStatus"] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    assert data["actions"] == [OrderAction.REFUND.name]
    txn = pay.transactions.get()
    assert data["transactions"] == [
        {
            "amount": {"currency": pay.currency, "amount": float(str(txn.amount))},
            "error": None,
            "gatewayResponse": "{}",
        }
    ]


QUERY_PAYMENT_BY_ID = """
    query payment($id: ID!) {
        payment(id: $id) {
            id
        }
    }
"""


def test_query_payment(payment_dummy, user_api_client, permission_manage_orders):
    query = QUERY_PAYMENT_BY_ID
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"id": payment_id}
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    received_id = content["data"]["payment"]["id"]
    assert received_id == payment_id


def test_staff_query_payment_by_invalid_id(
    staff_api_client, payment_dummy, permission_manage_orders
):
    id = "bh/"
    variables = {"id": id}
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_BY_ID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["payment"] is None


def test_staff_query_payment_with_invalid_object_type(
    staff_api_client, payment_dummy, permission_manage_orders
):
    variables = {"id": graphene.Node.to_global_id("Order", payment_dummy.pk)}
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_BY_ID, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    assert content["data"]["payment"] is None


def test_query_payments(payment_dummy, permission_manage_orders, staff_api_client):
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, {}, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    payment_ids = [edge["node"]["id"] for edge in edges]
    assert payment_ids == [payment_id]


def test_query_payments_filter_by_checkout(
    payment_dummy, checkouts_list, permission_manage_orders, staff_api_client
):
    # given
    payment1 = payment_dummy
    payment1.checkout = checkouts_list[0]
    payment1.save()

    payment2 = Payment.objects.get(id=payment1.id)
    payment2.id = None
    payment2.checkout = checkouts_list[1]
    payment2.save()

    payment3 = Payment.objects.get(id=payment1.id)
    payment3.id = None
    payment3.checkout = checkouts_list[2]
    payment3.save()

    variables = {
        "filter": {
            "checkouts": [
                graphene.Node.to_global_id("Checkout", checkout.pk)
                for checkout in checkouts_list[1:4]
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    payment_ids = {edge["node"]["id"] for edge in edges}
    assert payment_ids == {
        graphene.Node.to_global_id("Payment", payment.pk)
        for payment in [payment2, payment3]
    }


def test_query_payments_failed_payment(
    payment_txn_capture_failed, permission_manage_orders, staff_api_client
):
    # given
    payment = payment_txn_capture_failed

    # when
    response = staff_api_client.post_graphql(
        PAYMENT_QUERY, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["payments"]["edges"][0]["node"]

    assert data["gateway"] == payment.gateway
    amount = str(data["capturedAmount"]["amount"])
    assert Decimal(amount) == payment.captured_amount
    assert data["capturedAmount"]["currency"] == payment.currency
    total = str(data["total"]["amount"])
    assert Decimal(total) == payment.total
    assert data["total"]["currency"] == payment.currency
    assert data["chargeStatus"] == PaymentChargeStatusEnum.REFUSED.name
    assert data["actions"] == []
    txn = payment.transactions.get()
    assert data["transactions"] == [
        {
            "amount": {"currency": payment.currency, "amount": float(str(txn.amount))},
            "error": txn.error,
            "gatewayResponse": json.dumps(txn.gateway_response),
        }
    ]


@pytest.fixture
def braintree_customer_id():
    return "1234"


@pytest.fixture
def dummy_customer_id():
    return "4321"


def test_store_payment_gateway_meta(customer_user, braintree_customer_id):
    gateway_name = "braintree"
    meta_key = "BRAINTREE.customer_id"
    META = {meta_key: braintree_customer_id}
    store_customer_id(customer_user, gateway_name, braintree_customer_id)
    assert customer_user.private_metadata == META
    customer_user.refresh_from_db()
    assert fetch_customer_id(customer_user, gateway_name) == braintree_customer_id


@pytest.fixture
def token_config_with_customer(braintree_customer_id):
    return TokenConfig(customer_id=braintree_customer_id)


@pytest.fixture
def set_braintree_customer_id(customer_user, braintree_customer_id):
    gateway_name = "braintree"
    store_customer_id(customer_user, gateway_name, braintree_customer_id)
    return customer_user


@pytest.fixture
def set_dummy_customer_id(customer_user, dummy_customer_id):
    gateway_name = DUMMY_GATEWAY
    store_customer_id(customer_user, gateway_name, dummy_customer_id)
    return customer_user


def test_list_payment_sources(
    mocker, dummy_customer_id, set_dummy_customer_id, user_api_client, channel_USD
):
    metadata = {f"key_{i}": f"value_{i}" for i in range(5)}
    gateway = DUMMY_GATEWAY
    query = """
    {
        me {
            storedPaymentSources {
                gateway
                paymentMethodId
                creditCardInfo {
                    lastDigits
                    brand
                    firstDigits
                }
                metadata {
                    key
                    value
                }
            }
        }
    }
    """
    card = PaymentMethodInfo(
        last_4="5678",
        first_4="1234",
        exp_year=2020,
        exp_month=12,
        name="JohnDoe",
        brand="cardBrand",
    )
    source = CustomerSource(
        id="payment-method-id",
        gateway=gateway,
        credit_card_info=card,
        metadata=metadata,
    )
    mock_get_source_list = mocker.patch(
        "saleor.graphql.account.resolvers.gateway.list_payment_sources",
        return_value=[source],
        autospec=True,
    )
    response = user_api_client.post_graphql(query)

    mock_get_source_list.assert_called_once_with(gateway, dummy_customer_id, ANY, None)
    content = get_graphql_content(response)["data"]["me"]["storedPaymentSources"]
    assert content is not None and len(content) == 1
    assert content[0] == {
        "gateway": gateway,
        "paymentMethodId": "payment-method-id",
        "creditCardInfo": {
            "firstDigits": "1234",
            "lastDigits": "5678",
            "brand": "cardBrand",
        },
        "metadata": [{"key": key, "value": value} for key, value in metadata.items()],
    }


def test_stored_payment_sources_restriction(
    mocker, staff_api_client, customer_user, permission_manage_users
):
    # Only owner of storedPaymentSources can fetch it.
    card = PaymentMethodInfo(last_4="5678", exp_year=2020, exp_month=12, name="JohnDoe")
    source = CustomerSource(id="test1", gateway="dummy", credit_card_info=card)
    mocker.patch(
        "saleor.graphql.account.resolvers.gateway.list_payment_sources",
        return_value=[source],
        autospec=True,
    )

    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)
    query = """
        query PaymentSources($id: ID!) {
            user(id: $id) {
                storedPaymentSources {
                    creditCardInfo {
                        firstDigits
                    }
                }
            }
        }
    """
    variables = {"id": customer_user_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    assert_no_permission(response)


PAYMENT_INITIALIZE_MUTATION = """
mutation PaymentInitialize(
    $gateway: String!,$channel: String!, $paymentData: JSONString){
      paymentInitialize(gateway: $gateway, channel: $channel, paymentData: $paymentData)
      {
        initializedPayment{
          gateway
          name
          data
        }
        errors{
          field
          message
        }
      }
}
"""


@patch.object(PluginsManager, "initialize_payment")
def test_payment_initialize(mocked_initialize_payment, api_client, channel_USD):
    exected_initialize_payment_response = InitializedPaymentResponse(
        gateway="gateway.id",
        name="PaymentPluginName",
        data={
            "epochTimestamp": 1604652056653,
            "expiresAt": 1604655656653,
            "merchantSessionIdentifier": "SSH5EFCB46BA25C4B14B3F37795A7F5B974_BB8E",
        },
    )
    mocked_initialize_payment.return_value = exected_initialize_payment_response

    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": exected_initialize_payment_response.gateway,
        "channel": channel_USD.slug,
        "paymentData": json.dumps(
            {"paymentMethod": "applepay", "validationUrl": "https://127.0.0.1/valid"}
        ),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    init_payment_data = content["data"]["paymentInitialize"]["initializedPayment"]
    assert init_payment_data["gateway"] == exected_initialize_payment_response.gateway
    assert init_payment_data["name"] == exected_initialize_payment_response.name
    assert (
        json.loads(init_payment_data["data"])
        == exected_initialize_payment_response.data
    )


def test_payment_initialize_gateway_doesnt_exist(api_client, channel_USD):
    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": "wrong.gateway",
        "channel": channel_USD.slug,
        "paymentData": json.dumps(
            {"paymentMethod": "applepay", "validationUrl": "https://127.0.0.1/valid"}
        ),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["paymentInitialize"]["initializedPayment"] is None


@patch.object(PluginsManager, "initialize_payment")
def test_payment_initialize_plugin_raises_error(
    mocked_initialize_payment, api_client, channel_USD
):
    error_msg = "Missing paymentMethod field."
    mocked_initialize_payment.side_effect = PaymentError(error_msg)

    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": "gateway.id",
        "channel": channel_USD.slug,
        "paymentData": json.dumps({"validationUrl": "https://127.0.0.1/valid"}),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    initialized_payment_data = content["data"]["paymentInitialize"][
        "initializedPayment"
    ]
    errors = content["data"]["paymentInitialize"]["errors"]
    assert initialized_payment_data is None
    assert len(errors) == 1
    assert errors[0]["field"] == "paymentData"
    assert errors[0]["message"] == error_msg


QUERY_PAYMENT_REFUND_AMOUNT = """
     query payment($id: ID!) {
        payment(id: $id) {
            id,
            availableRefundAmount{
                amount
            }
            availableCaptureAmount{
                amount
            }
        }
    }
"""

QUERY_PAYMENT_CAPTURE_AMOUNT = """
     query payment($id: ID!) {
        payment(id: $id) {
            id,
            availableCaptureAmount{
                amount
            }
        }
    }
"""


def test_resolve_available_refund_amount_cannot_refund(
    staff_api_client, payment_cancelled, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_REFUND_AMOUNT,
        {"id": graphene.Node.to_global_id("Payment", payment_cancelled.pk)},
    )
    content = get_graphql_content(response)

    assert not content["data"]["payment"]["availableRefundAmount"]


def test_resolve_available_refund_amount(
    staff_api_client, payment_dummy_fully_charged, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_REFUND_AMOUNT,
        {"id": graphene.Node.to_global_id("Payment", payment_dummy_fully_charged.pk)},
    )
    content = get_graphql_content(response)

    assert content["data"]["payment"]["availableRefundAmount"]["amount"] == 98.4


def test_resolve_available_capture_amount_cannot_capture(
    staff_api_client, payment_cancelled, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_CAPTURE_AMOUNT,
        {"id": graphene.Node.to_global_id("Payment", payment_cancelled.pk)},
    )
    content = get_graphql_content(response)

    assert not content["data"]["payment"]["availableCaptureAmount"]


def test_resolve_available_capture_amount(
    staff_api_client, payment_dummy, permission_manage_orders
):
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_PAYMENT_CAPTURE_AMOUNT,
        {"id": graphene.Node.to_global_id("Payment", payment_dummy.pk)},
    )
    content = get_graphql_content(response)

    assert content["data"]["payment"]["availableCaptureAmount"]["amount"] == 98.4


MUTATION_CHECK_PAYMENT_BALANCE = """
    mutation checkPaymentBalance($input: PaymentCheckBalanceInput!) {
        paymentCheckBalance(input: $input){
            data
            errors {
                code
                field
                message
            }
        }
    }
"""


@patch.object(PluginsManager, "check_payment_balance")
def test_payment_check_balance_mutation_validate_gateway_does_not_exist(
    check_payment_balance_mock, staff_api_client, check_payment_balance_input
):
    check_payment_balance_input["gatewayId"] = "mirumee.payments.not_existing_gateway"
    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.value.upper()
    assert errors[0]["field"] == "gatewayId"
    assert errors[0]["message"] == (
        "The gateway_id mirumee.payments.not_existing_gateway is not available."
    )

    assert check_payment_balance_mock.call_count == 0


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch("saleor.graphql.channel.utils.validate_channel")
def test_payment_check_balance_validate_not_supported_currency(
    _, __, check_payment_balance_mock, staff_api_client, check_payment_balance_input
):
    check_payment_balance_input["card"]["money"]["currency"] = "ABSTRACT_CURRENCY"
    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.value.upper()
    assert errors[0]["field"] == "currency"
    assert errors[0]["message"] == (
        "The currency ABSTRACT_CURRENCY is not "
        "available for mirumee.payments.gateway."
    )

    assert check_payment_balance_mock.call_count == 0


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch.object(PaymentCheckBalance, "validate_currency")
def test_payment_check_balance_validate_channel_does_not_exist(
    _, __, check_payment_balance_mock, staff_api_client, check_payment_balance_input
):
    check_payment_balance_input["channel"] = "not_existing_channel"
    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.NOT_FOUND.value.upper()
    assert errors[0]["field"] == "channel"
    assert errors[0]["message"] == (
        "Channel with 'not_existing_channel' slug does not exist."
    )

    assert check_payment_balance_mock.call_count == 0


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch.object(PaymentCheckBalance, "validate_currency")
def test_payment_check_balance_validate_channel_inactive(
    _,
    __,
    check_payment_balance_mock,
    staff_api_client,
    channel_USD,
    check_payment_balance_input,
):
    channel_USD.is_active = False
    channel_USD.save(update_fields=["is_active"])
    check_payment_balance_input["channel"] = "main"

    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.CHANNEL_INACTIVE.value.upper()
    assert errors[0]["field"] == "channel"
    assert errors[0]["message"] == "Channel with 'main' is inactive."
    assert check_payment_balance_mock.call_count == 0


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch.object(PaymentCheckBalance, "validate_currency")
@patch("saleor.graphql.payment.mutations.validate_channel")
def test_payment_check_balance_payment(
    _,
    __,
    ___,
    check_payment_balance_mock,
    staff_api_client,
    check_payment_balance_input,
):
    staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    check_payment_balance_mock.assert_called_once_with(
        {
            "gateway_id": "mirumee.payments.gateway",
            "method": "givex",
            "card": {
                "cvc": "9891",
                "code": "12345678910",
                "money": {"currency": "GBP", "amount": 100.0},
            },
        },
        "channel_default",
    )


@patch.object(PluginsManager, "check_payment_balance")
@patch.object(PaymentCheckBalance, "validate_gateway")
@patch.object(PaymentCheckBalance, "validate_currency")
@patch("saleor.graphql.payment.mutations.validate_channel")
def test_payment_check_balance_balance_raises_error(
    _,
    __,
    ___,
    check_payment_balance_mock,
    staff_api_client,
    check_payment_balance_input,
):
    check_payment_balance_mock.side_effect = Mock(
        side_effect=PaymentError("Test payment error")
    )

    response = staff_api_client.post_graphql(
        MUTATION_CHECK_PAYMENT_BALANCE, {"input": check_payment_balance_input}
    )

    content = get_graphql_content(response)
    errors = content["data"]["paymentCheckBalance"]["errors"]

    assert len(errors) == 1
    assert errors[0]["code"] == PaymentErrorCode.BALANCE_CHECK_ERROR.value.upper()
    assert errors[0]["message"] == "Test payment error"

    check_payment_balance_mock.assert_called_once_with(
        {
            "gateway_id": "mirumee.payments.gateway",
            "method": "givex",
            "card": {
                "cvc": "9891",
                "code": "12345678910",
                "money": {"currency": "GBP", "amount": 100.0},
            },
        },
        "channel_default",
    )
