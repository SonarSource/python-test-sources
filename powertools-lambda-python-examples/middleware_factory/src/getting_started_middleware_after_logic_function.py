import time
from typing import Callable

import requests
from requests import Response

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver()


@lambda_handler_decorator
def middleware_after(
    handler: Callable[[dict, LambdaContext], dict],
    event: dict,
    context: LambdaContext,
) -> dict:
    start_time = time.time()
    response = handler(event, context)
    execution_time = time.time() - start_time

    # adding custom headers in response object after lambda executing
    response["headers"]["execution_time"] = execution_time
    response["headers"]["aws_request_id"] = context.aws_request_id

    return response


@app.post("/todos")
def create_todo() -> dict:
    todo_data: dict = app.current_event.json_body  # deserialize json str to dict
    todo: Response = requests.post("https://jsonplaceholder.typicode.com/todos", data=todo_data)
    todo.raise_for_status()

    return {"todo": todo.json()}


@middleware_after
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
