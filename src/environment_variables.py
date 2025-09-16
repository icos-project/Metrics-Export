import os
import logging


def str_to_bool(value):
    return str(value).lower() in ("true", "1", "yes")


# set a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT = int(os.getenv('INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT', 60))


# INTELLIGENCE_API_MODEL_INFERENCE_BASE_URL = os.getenv('INTELLIGENCE_API_BASE_URL', 'http://10.160.3.160:3000/') + 'predict'
# INTELLIGENCE_API_MODEL_TRAINING_URL = os.getenv('INTELLIGENCE_API_BASE_URL', 'http://10.160.3.160:3000/') + 'train'
# INTELLIGENCE_API_SHOW_MODELS = os.getenv('INTELLIGENCE_API_BASE_URL', 'http://10.160.3.160:3000/') + 'show_models'
# INTELLIGENCE_API_REMOVE_MODEL = os.getenv('INTELLIGENCE_API_BASE_URL', 'http://10.160.3.160:3000/') + 'remove_model'
# INTELLIGENCE_API_MODEL_INFERENCE_BASE_URL = 'http://10.160.3.160:3000/predict'
# INTELLIGENCE_API_MODEL_TRAINING_URL = 'http://10.160.3.160:3000/train_model'
# INTELLIGENCE_API_SHOW_MODELS = 'http://10.160.3.160:3000/show_models'
# INTELLIGENCE_API_REMOVE_MODEL = 'http://10.160.3.160:3000/remove_model'
def get_intelligence_api_url(url_route: str, url_base_path: str = ''):
    if url_base_path == '':
        # return os.getenv('INTELLIGENCE_API_BASE_URL', 'http://10.160.3.160:3000/') + url_route
        return os.getenv('INTELLIGENCE_API_BASE_URL', 'http://10.160.3.20:30600/') + url_route
    return 'http://' + url_base_path + '/' + url_route


# NKUA
# GRAFANA_API_BASE_URL = os.getenv('GRAFANA_API_BASE_URL', 'http://91.138.223.127:30009/')
# NCSRD
GRAFANA_API_BASE_URL = os.getenv('GRAFANA_API_BASE_URL', 'http://10.160.3.20:32100/')

#NCSRD new
GRAFANA_SERVICE_ACCOUNT_BEARER_TOKEN = os.getenv('GRAFANA_SERVICE_ACCOUNT_BEARER_TOKEN', 'glsa_ZtX8mEMViiHt9k66RBmgfpxFgKU54xAi_acca5d94')

GRAFANA_INTERVAL_MS = int(os.getenv('GRAFANA_INTERVAL_MS', 60000))
GRAFANA_UTC_OFFSET_SEC = int(os.getenv('GRAFANA_UTC_OFFSET', 7200))

# NKUA
# GRAFANA_DATASOURCE_UID = os.getenv('GRAFANA_DATASOURCE_UID', 'PBFA97CFB590B2093')
# NCSRD
GRAFANA_DATASOURCE_UID = os.getenv('GRAFANA_DATASOURCE_UID', 'a151c53f-db08-4d10-a3b8-97ef5f2d614f')

# DATACLAY_HOST = os.getenv('DATACLAY_HOST', '127.0.0.1')
# DATACLAY_USERNAME = os.getenv('DATACLAY_USERNAME', 'testuser')
# DATACLAY_PASSWORD = os.getenv('DATACLAY_PASSWORD', 's3cret')
DATACLAY_HOST = os.getenv('DATACLAY_HOST', '')
DATACLAY_USERNAME = os.getenv('DATACLAY_USERNAME', '')
DATACLAY_PASSWORD = os.getenv('DATACLAY_PASSWORD', '')

PROMETHEUS_METRICS_DISABLED = str_to_bool(os.getenv('PROMETHEUS_METRICS_DISABLED', 'False'))
SECURITY_DISABLED = str_to_bool(os.getenv('SECURITY_DISABLED', 'True'))

KEYCLOAK_SERVER_URL = os.getenv('KEYCLOAK_SERVER_URL', 'https://iam.core.icos-staging.10-160-3-151.sslip.io/')
KEYCLOAK_REALM_NAME = os.getenv('KEYCLOAK_REALM_NAME', 'staging-continuum')
KEYCLOAK_RESOURCE_SERVER_ID = os.getenv('KEYCLOAK_RESOURCE_SERVER_ID', 'Default Resource')
KEYCLOAK_AUDIENCE = os.getenv('KEYCLOAK_AUDIENCE', 'Default Resource')
KEYCLOAK_CLIENT_ID = os.getenv('KEYCLOAK_CLIENT_ID', 'contrl-1.metrics-exporter')
KEYCLOAK_CLIENT_SECRET_KEY = os.getenv('KEYCLOAK_CLIENT_SECRET_KEY', 'MNIqnJY76KilvzYAvoxMfTCiTYZA68Aa')

AGGREGATOR_URL = os.getenv('AGGREGATOR_URL', 'http://10.160.3.20:30400/')
