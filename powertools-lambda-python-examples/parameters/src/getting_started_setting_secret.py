from typing import Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger(serialize_stacktrace=True)


def access_token(client_id: str, client_secret: str, audience: str) -> str:
    # example function that returns a JWT Access Token
    # add your own logic here
    return f"{client_id}.{client_secret}.{audience}"


def lambda_handler(event: dict, context: LambdaContext):
    try:
        client_id: Any = parameters.get_parameter("/aws-powertools/client_id")
        client_secret: Any = parameters.get_parameter("/aws-powertools/client_secret")
        audience: Any = parameters.get_parameter("/aws-powertools/audience")

        jwt_token = access_token(client_id=client_id, client_secret=client_secret, audience=audience)

        # set-secret will create a new secret if it doesn't exist and return the version id
        update_secret_version_id = parameters.set_secret(name="/aws-powertools/jwt_token", value=jwt_token)

        return {"access_token": "updated", "statusCode": 200, "update_secret_version_id": update_secret_version_id}
    except parameters.exceptions.SetSecretError as error:
        logger.exception(error)
        return {"access_token": "updated", "statusCode": 400}
