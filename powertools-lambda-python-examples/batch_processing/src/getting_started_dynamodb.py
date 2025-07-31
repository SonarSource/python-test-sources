import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.DynamoDBStreams)  # (1)!
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: DynamoDBRecord):
    if record.dynamodb and record.dynamodb.new_image:
        logger.info(record.dynamodb.new_image)
        message = record.dynamodb.new_image.get("Message")
        if message:
            payload: dict = json.loads(message)
            logger.info(payload)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
