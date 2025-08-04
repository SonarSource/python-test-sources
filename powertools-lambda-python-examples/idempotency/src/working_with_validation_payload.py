import os
from dataclasses import dataclass, field
from uuid import uuid4

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.exceptions import IdempotencyValidationError
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

table = os.getenv("IDEMPOTENCY_TABLE", "")
persistence_layer = DynamoDBPersistenceLayer(table_name=table)
config = IdempotencyConfig(
    event_key_jmespath='["user_id", "product_id"]',
    payload_validation_jmespath="amount",
)


@dataclass
class Payment:
    user_id: str
    product_id: str
    charge_type: str
    amount: int
    payment_id: str = field(default_factory=lambda: f"{uuid4()}")


class PaymentError(Exception): ...


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext):
    try:
        payment: Payment = create_subscription_payment(event)
        return {
            "payment_id": payment.payment_id,
            "message": "success",
            "statusCode": 200,
        }
    except IdempotencyValidationError:
        logger.exception("Payload tampering detected", payment=payment, failure_type="validation")
        return {
            "message": "Unable to process payment at this time. Try again later.",
            "statusCode": 500,
        }
    except Exception as exc:
        raise PaymentError(f"Error creating payment {str(exc)}")


def create_subscription_payment(event: dict) -> Payment:
    return Payment(**event)
