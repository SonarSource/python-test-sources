import json
import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List, Optional, cast

import graphene
from babel.numbers import get_currency_precision
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q

from ..account.models import User
from ..checkout.models import Checkout
from ..core.prices import quantize_price
from ..core.tracing import traced_atomic_transaction
from ..order.models import Order
from . import (
    ChargeStatus,
    GatewayError,
    PaymentError,
    StorePaymentMethod,
    TransactionKind,
)
from .error_codes import PaymentErrorCode
from .interface import (
    AddressData,
    GatewayResponse,
    PaymentData,
    PaymentMethodInfo,
    StorePaymentMethodEnum,
)
from .models import Payment, Transaction

if TYPE_CHECKING:
    from ..plugins.manager import PluginsManager

logger = logging.getLogger(__name__)

GENERIC_TRANSACTION_ERROR = "Transaction was unsuccessful"
ALLOWED_GATEWAY_KINDS = {choices[0] for choices in TransactionKind.CHOICES}


def create_payment_information(
    payment: Payment,
    payment_token: str = None,
    amount: Decimal = None,
    customer_id: str = None,
    store_source: bool = False,
    additional_data: Optional[dict] = None,
) -> PaymentData:
    """Extract order information along with payment details.

    Returns information required to process payment and additional
    billing/shipping addresses for optional fraud-prevention mechanisms.
    """
    if checkout := payment.checkout:
        billing = checkout.billing_address
        shipping = checkout.shipping_address
        email = cast(str, checkout.get_customer_email())
        user_id = checkout.user_id
        checkout_token = str(checkout.token)
        checkout_metadata = checkout.metadata
    elif order := payment.order:
        billing = order.billing_address
        shipping = order.shipping_address
        email = order.user_email
        user_id = order.user_id
        checkout_token = order.checkout_token
        checkout_metadata = None
    else:
        billing = None
        shipping = None
        email = payment.billing_email
        user_id = None
        checkout_token = ""
        checkout_metadata = None

    billing_address = AddressData(**billing.as_data()) if billing else None
    shipping_address = AddressData(**shipping.as_data()) if shipping else None

    order_id = payment.order.pk if payment.order else None
    graphql_payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    graphql_customer_id = None
    if user_id:
        graphql_customer_id = graphene.Node.to_global_id("User", user_id)

    return PaymentData(
        gateway=payment.gateway,
        token=payment_token,
        amount=amount or payment.total,
        currency=payment.currency,
        billing=billing_address,
        shipping=shipping_address,
        order_id=order_id,
        payment_id=payment.pk,
        graphql_payment_id=graphql_payment_id,
        customer_ip_address=payment.customer_ip_address,
        customer_id=customer_id,
        customer_email=email,
        reuse_source=store_source,
        data=additional_data or {},
        graphql_customer_id=graphql_customer_id,
        store_payment_method=StorePaymentMethodEnum[
            payment.store_payment_method.upper()
        ],
        checkout_token=checkout_token,
        checkout_metadata=checkout_metadata,
        payment_metadata=payment.metadata,
        psp_reference=payment.psp_reference,
    )


def create_payment(
    gateway: str,
    total: Decimal,
    currency: str,
    email: str,
    customer_ip_address: str = "",
    payment_token: Optional[str] = "",
    extra_data: Dict = None,
    checkout: Checkout = None,
    order: Order = None,
    return_url: str = None,
    external_reference: Optional[str] = None,
    store_payment_method: str = StorePaymentMethod.NONE,
    metadata: Optional[Dict[str, str]] = None,
) -> Payment:
    """Create a payment instance.

    This method is responsible for creating payment instances that works for
    both Django views and GraphQL mutations.
    """

    if extra_data is None:
        extra_data = {}

    data = {
        "is_active": True,
        "customer_ip_address": customer_ip_address,
        "extra_data": json.dumps(extra_data),
        "token": payment_token,
    }

    if checkout:
        data["checkout"] = checkout
        billing_address = checkout.billing_address
    elif order:
        data["order"] = order
        billing_address = order.billing_address
    else:
        raise TypeError("Must provide checkout or order to create a payment.")

    if not billing_address:
        raise PaymentError(
            "Order does not have a billing address.",
            code=PaymentErrorCode.BILLING_ADDRESS_NOT_SET.value,
        )

    defaults = {
        "billing_email": email,
        "billing_first_name": billing_address.first_name,
        "billing_last_name": billing_address.last_name,
        "billing_company_name": billing_address.company_name,
        "billing_address_1": billing_address.street_address_1,
        "billing_address_2": billing_address.street_address_2,
        "billing_city": billing_address.city,
        "billing_postal_code": billing_address.postal_code,
        "billing_country_code": billing_address.country.code,
        "billing_country_area": billing_address.country_area,
        "currency": currency,
        "gateway": gateway,
        "total": total,
        "return_url": return_url,
        "partial": False,
        "psp_reference": external_reference or "",
        "store_payment_method": store_payment_method,
        "metadata": {} if metadata is None else metadata,
    }

    payment, _ = Payment.objects.get_or_create(defaults=defaults, **data)
    return payment


def get_already_processed_transaction(
    payment: "Payment", gateway_response: GatewayResponse
):
    transaction = payment.transactions.filter(
        is_success=gateway_response.is_success,
        action_required=gateway_response.action_required,
        token=gateway_response.transaction_id,
        kind=gateway_response.kind,
        amount=gateway_response.amount,
        currency=gateway_response.currency,
    ).last()
    return transaction


def create_transaction(
    payment: Payment,
    kind: str,
    payment_information: PaymentData,
    action_required: bool = False,
    gateway_response: GatewayResponse = None,
    error_msg=None,
    is_success=False,
) -> Transaction:
    """Create a transaction based on transaction kind and gateway response."""
    # Default values for token, amount, currency are only used in cases where
    # response from gateway was invalid or an exception occurred
    if not gateway_response:
        gateway_response = GatewayResponse(
            kind=kind,
            action_required=False,
            transaction_id=payment_information.token or "",
            is_success=is_success,
            amount=payment_information.amount,
            currency=payment_information.currency,
            error=error_msg,
            raw_response={},
        )

    txn = Transaction.objects.create(
        payment=payment,
        action_required=action_required,
        kind=gateway_response.kind,
        token=gateway_response.transaction_id,
        is_success=gateway_response.is_success,
        amount=gateway_response.amount,
        currency=gateway_response.currency,
        error=gateway_response.error,
        customer_id=gateway_response.customer_id,
        gateway_response=gateway_response.raw_response or {},
        action_required_data=gateway_response.action_required_data or {},
    )
    return txn


def get_already_processed_transaction_or_create_new_transaction(
    payment: Payment,
    kind: str,
    payment_information: PaymentData,
    action_required: bool = False,
    gateway_response: GatewayResponse = None,
    error_msg=None,
) -> Transaction:
    if gateway_response and gateway_response.transaction_already_processed:
        txn = get_already_processed_transaction(payment, gateway_response)
        if txn:
            return txn
    return create_transaction(
        payment,
        kind,
        payment_information,
        action_required,
        gateway_response,
        error_msg,
    )


def clean_capture(payment: Payment, amount: Decimal):
    """Check if payment can be captured."""
    if amount <= 0:
        raise PaymentError("Amount should be a positive number.")
    if not payment.can_capture():
        raise PaymentError("This payment cannot be captured.")
    if amount > payment.total or amount > (payment.total - payment.captured_amount):
        raise PaymentError("Unable to charge more than un-captured amount.")


def clean_authorize(payment: Payment):
    """Check if payment can be authorized."""
    if not payment.can_authorize():
        raise PaymentError("Charged transactions cannot be authorized again.")


def validate_gateway_response(response: GatewayResponse):
    """Validate response to be a correct format for Saleor to process."""
    if not isinstance(response, GatewayResponse):
        raise GatewayError("Gateway needs to return a GatewayResponse obj")

    if response.kind not in ALLOWED_GATEWAY_KINDS:
        raise GatewayError(
            "Gateway response kind must be one of {}".format(
                sorted(ALLOWED_GATEWAY_KINDS)
            )
        )

    try:
        json.dumps(response.raw_response, cls=DjangoJSONEncoder)
    except (TypeError, ValueError):
        raise GatewayError("Gateway response needs to be json serializable")


@traced_atomic_transaction()
def gateway_postprocess(transaction, payment):
    changed_fields = []

    if not transaction.is_success or transaction.already_processed:
        if changed_fields:
            payment.save(update_fields=changed_fields)
        return

    if transaction.action_required:
        payment.to_confirm = True
        changed_fields.append("to_confirm")
        payment.save(update_fields=changed_fields)
        return

    # to_confirm is defined by the transaction.action_required. Payment doesn't
    # require confirmation when we got action_required == False
    if payment.to_confirm:
        payment.to_confirm = False
        changed_fields.append("to_confirm")

    update_payment_charge_status(payment, transaction, changed_fields)


def update_payment_charge_status(payment, transaction, changed_fields=None):
    changed_fields = changed_fields or []

    transaction_kind = transaction.kind

    if transaction_kind in {
        TransactionKind.CAPTURE,
        TransactionKind.REFUND_REVERSED,
    }:
        payment.captured_amount += transaction.amount
        payment.is_active = True
        # Set payment charge status to fully charged
        # only if there is no more amount needs to charge
        payment.charge_status = ChargeStatus.PARTIALLY_CHARGED
        if payment.get_charge_amount() <= 0:
            payment.charge_status = ChargeStatus.FULLY_CHARGED
        changed_fields += ["charge_status", "captured_amount", "modified"]

    elif transaction_kind == TransactionKind.VOID:
        payment.is_active = False
        changed_fields += ["is_active", "modified"]

    elif transaction_kind == TransactionKind.REFUND:
        changed_fields += ["captured_amount", "modified"]
        payment.captured_amount -= transaction.amount
        payment.charge_status = ChargeStatus.PARTIALLY_REFUNDED
        if payment.captured_amount <= 0:
            payment.captured_amount = Decimal("0.0")
            payment.charge_status = ChargeStatus.FULLY_REFUNDED
            payment.is_active = False
        changed_fields += ["charge_status", "is_active"]
    elif transaction_kind == TransactionKind.PENDING:
        payment.charge_status = ChargeStatus.PENDING
        changed_fields += ["charge_status"]
    elif transaction_kind == TransactionKind.CANCEL:
        payment.charge_status = ChargeStatus.CANCELLED
        payment.is_active = False
        changed_fields += ["charge_status", "is_active"]
    elif transaction_kind == TransactionKind.CAPTURE_FAILED:
        if payment.charge_status in {
            ChargeStatus.PARTIALLY_CHARGED,
            ChargeStatus.FULLY_CHARGED,
        }:
            payment.captured_amount -= transaction.amount
            payment.charge_status = ChargeStatus.PARTIALLY_CHARGED
            if payment.captured_amount <= 0:
                payment.charge_status = ChargeStatus.NOT_CHARGED
            changed_fields += ["charge_status", "captured_amount", "modified"]
    if changed_fields:
        payment.save(update_fields=changed_fields)
    transaction.already_processed = True
    transaction.save(update_fields=["already_processed"])
    if "captured_amount" in changed_fields and payment.order:
        payment.order.update_total_paid()


def fetch_customer_id(user: User, gateway: str):
    """Retrieve users customer_id stored for desired gateway."""
    meta_key = prepare_key_for_gateway_customer_id(gateway)
    return user.get_value_from_private_metadata(key=meta_key)


def store_customer_id(user: User, gateway: str, customer_id: str):
    """Store customer_id in users private meta for desired gateway."""
    meta_key = prepare_key_for_gateway_customer_id(gateway)
    user.store_value_in_private_metadata(items={meta_key: customer_id})
    user.save(update_fields=["private_metadata"])


def prepare_key_for_gateway_customer_id(gateway_name: str) -> str:
    return (gateway_name.strip().upper()) + ".customer_id"


def update_payment(payment: "Payment", gateway_response: "GatewayResponse"):
    changed_fields = []
    if psp_reference := gateway_response.psp_reference:
        payment.psp_reference = psp_reference
        changed_fields.append("psp_reference")

    if gateway_response.payment_method_info:
        update_payment_method_details(
            payment, gateway_response.payment_method_info, changed_fields
        )

    if changed_fields:
        payment.save(update_fields=changed_fields)


def update_payment_method_details(
    payment: "Payment",
    payment_method_info: Optional["PaymentMethodInfo"],
    changed_fields: List[str],
):
    if not payment_method_info:
        return
    if payment_method_info.brand:
        payment.cc_brand = payment_method_info.brand
        changed_fields.append("cc_brand")
    if payment_method_info.last_4:
        payment.cc_last_digits = payment_method_info.last_4
        changed_fields.append("cc_last_digits")
    if payment_method_info.exp_year:
        payment.cc_exp_year = payment_method_info.exp_year
        changed_fields.append("cc_exp_year")
    if payment_method_info.exp_month:
        payment.cc_exp_month = payment_method_info.exp_month
        changed_fields.append("cc_exp_month")
    if payment_method_info.type:
        payment.payment_method_type = payment_method_info.type
        changed_fields.append("payment_method_type")


def get_payment_token(payment: Payment):
    auth_transaction = payment.transactions.filter(
        kind=TransactionKind.AUTH, is_success=True
    ).first()
    if auth_transaction is None:
        raise PaymentError("Cannot process unauthorized transaction")
    return auth_transaction.token


def is_currency_supported(currency: str, gateway_id: str, manager: "PluginsManager"):
    """Return true if the given gateway supports given currency."""
    available_gateways = manager.list_payment_gateways(currency=currency)
    return any([gateway.id == gateway_id for gateway in available_gateways])


def price_from_minor_unit(value: str, currency: str):
    """Convert minor unit (smallest unit of currency) to decimal value.

    (value: 1000, currency: USD) will be converted to 10.00
    """

    value = Decimal(value)
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return value * number_places


def price_to_minor_unit(value: Decimal, currency: str):
    """Convert decimal value to the smallest unit of currency.

    Take the value, discover the precision of currency and multiply value by
    Decimal('10.0'), then change quantization to remove the comma.
    Decimal(10.0) -> str(1000)
    """
    value = quantize_price(value, currency=currency)
    precision = get_currency_precision(currency)
    number_places = Decimal("10.0") ** precision
    value_without_comma = value * number_places
    return str(value_without_comma.quantize(Decimal("1")))


def payment_owned_by_user(payment_pk: int, user) -> bool:
    if user.is_anonymous:
        return False
    return (
        Payment.objects.filter(
            (Q(order__user=user) | Q(checkout__user=user)) & Q(pk=payment_pk)
        ).first()
        is not None
    )
