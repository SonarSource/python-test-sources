from typing import List, Optional

import requests
from requests import Response

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.get("/todos")
@tracer.capture_method
def get_todos():
    todo_id: str = app.current_event.query_string_parameters["id"]
    # alternatively
    _: Optional[str] = app.current_event.query_string_parameters.get("id")

    # or multi-value query string parameters; ?category="red"&?category="blue"
    _: List[str] = app.current_event.multi_value_query_string_parameters["category"]

    # Payload
    _: Optional[str] = app.current_event.body  # raw str | None

    endpoint = "https://jsonplaceholder.typicode.com/todos"
    if todo_id:
        endpoint = f"{endpoint}/{todo_id}"

    todos: Response = requests.get(endpoint)
    todos.raise_for_status()

    return {"todos": todos.json()}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
