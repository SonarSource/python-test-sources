from typing import List, TypedDict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils
from aws_lambda_powertools.utilities.data_classes.appsync_resolver_event import (
    AppSyncResolverEvent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = AppSyncResolver()


class Location(TypedDict, total=False):
    id: str  # noqa AA03 VNE003, required due to GraphQL Schema
    name: str
    description: str
    address: str
    commonField: str


class MyCustomModel(AppSyncResolverEvent):
    @property
    def country_viewer(self) -> str:
        return self.request_headers.get("cloudfront-viewer-country", "")

    @property
    def api_key(self) -> str:
        return self.request_headers.get("x-api-key", "")


@app.resolver(type_name="Query", field_name="listLocations")
def list_locations(page: int = 0, size: int = 10) -> List[Location]:
    # additional properties/methods will now be available under current_event
    if app.current_event:
        logger.debug(f"Request country origin: {app.current_event.country_viewer}")  # type: ignore[attr-defined]
    return [{"id": scalar_types_utils.make_id(), "name": "Perry, James and Carroll"}]


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context, data_model=MyCustomModel)
