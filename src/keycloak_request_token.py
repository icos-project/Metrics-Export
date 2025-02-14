import requests

from src.environment_variables import KEYCLOAK_SERVER_URL, KEYCLOAK_REALM_NAME, KEYCLOAK_CLIENT_ID, \
    KEYCLOAK_CLIENT_SECRET_KEY, logger

# Define the URL and credentials
# url_keycloak = 'https://iam.core.icos-staging.10-160-3-151.sslip.io/realms/staging-continuum/protocol/openid-connect/token'
url_keycloak = KEYCLOAK_SERVER_URL + 'realms/' + KEYCLOAK_REALM_NAME + '/protocol/openid-connect/token'
data = {
    'client_id': KEYCLOAK_CLIENT_ID,
    'client_secret': KEYCLOAK_CLIENT_SECRET_KEY,
    'grant_type': 'client_credentials'
}


def keycloak_request_token():
    # Make the POST request with SSL verification disabled (equivalent to -k in curl)
    # response = requests.post(url_keycloak, data=data, verify=False)
    response = requests.post(url_keycloak, data=data)
    # Extract access token if the request was successful
    if response.status_code == 200:
        access_token = response.json().get('access_token')
        logger.info('Successfully retrieved Access Token: {}'.format(access_token))
        return access_token
    else:
        logger.error('Error: {}, {}'.format(response.status_code, response.text))
