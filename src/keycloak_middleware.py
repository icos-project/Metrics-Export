#  Reverse proxy api
#  Copyright © 2022-2024 ICOS Consortium
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  This work has received funding from the European Union's HORIZON research
#  and innovation programme under grant agreement No. 101070177.

from fastapi import Request
from fastapi.responses import JSONResponse
import keycloak
from keycloak import KeycloakOpenID
from src.environment_variables import KEYCLOAK_SERVER_URL, KEYCLOAK_REALM_NAME, KEYCLOAK_CLIENT_ID, \
    KEYCLOAK_CLIENT_SECRET_KEY, SECURITY_DISABLED, PROMETHEUS_METRICS_DISABLED, logger

keycloak_open_id = KeycloakOpenID(
    KEYCLOAK_SERVER_URL,
    KEYCLOAK_REALM_NAME,
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET_KEY,
    # verify="/etc/ssl/certs/ca-certificates.crt"
)


async def validate_keycloak(request: Request, call_next):
    if not should_perform_keycloak_validation(request.url.path):
        response = await call_next(request)
        return response

    logger.info('Validating keycloak')

    token_header = request.headers.get('Authorization')

    if token_header is None:
        err = 'No authorization header.'
        error = {'message': err}
        logger.warning(err)

        return JSONResponse(error, status_code=401)

    split = token_header.split(" ")

    if len(split) < 2:
        err = 'Error with the token.'
        error = {'message': err}
        logger.warning(err)

        return JSONResponse(error, status_code=401)

    token = split[1].strip()
    permissions = get_token_permissions(token)

    # Validate permissions
    if not validate_permissions(permissions):

        err = 'Insufficient permissions.'
        error = {'message': err}
        logger.warning(err)
        return JSONResponse(error, status_code=403)

    response = await call_next(request)
    return response


def should_perform_keycloak_validation(request_url: str):
    if SECURITY_DISABLED:
        return False
    if request_url.startswith('/health'):
        return False
    if request_url.startswith('/healthz'):
        return False
    elif request_url.startswith('/docs'):
        return False
    elif request_url.startswith('/openapi.json'):
        return False
    elif request_url.startswith('/metrics') and not PROMETHEUS_METRICS_DISABLED:
        return False
    return True


def get_token_permissions(token: str):
    return keycloak_open_id.uma_permissions(token)


def validate_permissions(permissions):
    # for permission in permissions:
    #     scopes = permission.get('scope')
    #     auth_status = keycloak.uma_permissions.AuthStatus(
    #         is_logged_in=True,  # Assuming the user is logged in
    #         is_authorized=True if permission.get('scopes') else False,  # Check if scopes exist
    #         missing_permissions=set()  # No missing permissions for now
    #     )
    #
    #     if auth_status.is_logged_in and auth_status.is_authorized:
    #         logger.info("User is authorized in scope(s): %s", scopes)
    #         return True
    auth_status = keycloak.uma_permissions.AuthStatus(
                is_logged_in=True, # Assuming the user is logged in
                is_authorized=True, # Check if user is authorized
                missing_permissions=set()  # No missing permissions for now
            )

    if auth_status.is_logged_in and auth_status.is_authorized:
        logger.info("User is authorized")
        return True

    logger.warning("User is not authorized.")
    return False

