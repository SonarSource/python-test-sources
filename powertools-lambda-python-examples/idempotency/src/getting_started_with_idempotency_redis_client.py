import os
from dataclasses import dataclass, field
from uuid import uuid4

from redis import Redis

from aws_lambda_powertools.utilities.idempotency import (
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.persistence.cache import (
    CachePersistenceLayer,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

cache_endpoint = os.getenv("CACHE_CLUSTER_ENDPOINT", "localhost")
client = Redis(
    host=cache_endpoint,
    port=6379,
    socket_connect_timeout=5,
    socket_timeout=5,
    max_connections=1000,
)

persistence_layer = CachePersistenceLayer(client=client)


@dataclass
class Payment:
    user_id: str
    product_id: str
    payment_id: str = field(default_factory=lambda: f"{uuid4()}")


class PaymentError(Exception): ...


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event: dict, context: LambdaContext):
    try:
        payment: Payment = create_subscription_payment(event)
        return {
            "payment_id": payment.payment_id,
            "message": "success",
            "statusCode": 200,
        }
    except Exception as exc:
        raise PaymentError(f"Error creating payment {str(exc)}")


def create_subscription_payment(event: dict) -> Payment:
    return Payment(**event)
