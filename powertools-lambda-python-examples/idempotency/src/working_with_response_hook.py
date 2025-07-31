import os
import uuid
from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import (
    DataRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def my_response_hook(response: Dict, idempotent_data: DataRecord) -> Dict:
    # Return inserted Header data into the Idempotent Response
    response["x-idempotent-key"] = idempotent_data.idempotency_key

    # expiry_timestamp can be None so include if set
    expiry_timestamp = idempotent_data.get_expiration_datetime()
    if expiry_timestamp:
        response["x-idempotent-expiration"] = expiry_timestamp.isoformat()

    # Must return the response here
    return response


table = os.getenv("IDEMPOTENCY_TABLE", "")
dynamodb = DynamoDBPersistenceLayer(table_name=table)
config = IdempotencyConfig(response_hook=my_response_hook)


@idempotent_function(data_keyword_argument="order", config=config, persistence_store=dynamodb)
def process_order(order: dict) -> dict:
    # create the order_id
    order_id = str(uuid.uuid4())

    # create your logic to save the order
    # append the order_id created
    order["order_id"] = order_id

    # return the order
    return {"order": order}


def lambda_handler(event: dict, context: LambdaContext):
    config.register_lambda_context(context)  # see Lambda timeouts section
    try:
        logger.info(f"Processing order id {event.get('order_id')}")
        return process_order(order=event.get("order"))
    except Exception as err:
        return {"status_code": 400, "error": f"Error processing {str(err)}"}
