from secrets import compare_digest

from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.api_gateway_authorizer_event import (
    APIGatewayAuthorizerEventV2,
    APIGatewayAuthorizerResponseV2,
)


def get_user_by_token(token):
    if compare_digest(token, "value"):
        return {"name": "Foo"}
    return None


@event_source(data_class=APIGatewayAuthorizerEventV2)
def lambda_handler(event: APIGatewayAuthorizerEventV2, context):
    user = get_user_by_token(event.headers.get("Authorization"))

    if user is None:
        # No user was found, so we return not authorized
        return APIGatewayAuthorizerResponseV2(authorize=False).asdict()

    # Found the user and setting the details in the context
    response = APIGatewayAuthorizerResponseV2(
        authorize=True,
        context=user,
    )

    return response.asdict()
