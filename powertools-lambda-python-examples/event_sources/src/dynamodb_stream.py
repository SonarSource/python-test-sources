from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecordEventName,
    DynamoDBStreamEvent,
)


def lambda_handler(event, context):
    event: DynamoDBStreamEvent = DynamoDBStreamEvent(event)

    # Multiple records can be delivered in a single event
    for record in event.records:
        if record.event_name == DynamoDBRecordEventName.MODIFY:
            pass
        elif record.event_name == DynamoDBRecordEventName.INSERT:
            pass
    return "success"
