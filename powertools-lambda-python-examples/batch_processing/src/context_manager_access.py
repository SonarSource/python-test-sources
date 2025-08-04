from __future__ import annotations

import json

from typing_extensions import Literal

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.SQS)
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: SQSRecord):
    payload: str = record.body
    if payload:
        item: dict = json.loads(payload)
        logger.info(item)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    batch = event["Records"]  # (1)!
    with processor(records=batch, handler=record_handler):
        processed_messages: list[tuple] = processor.process()

    for message in processed_messages:
        status: Literal["success", "fail"] = message[0]
        cause: str = message[1]  # (2)!
        record: SQSRecord = message[2]

        logger.info(status, record=record, cause=cause)

    return processor.response()
