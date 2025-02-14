import json
import time
import requests
from src.environment_variables import GRAFANA_API_BASE_URL, GRAFANA_INTERVAL_MS, GRAFANA_UTC_OFFSET_SEC, \
    GRAFANA_DATASOURCE_UID, GRAFANA_SERVICE_ACCOUNT_BEARER_TOKEN, logger
from src.utilities import format_metric_string

# Grafana URL and Prometheus Data Source
grafana_url = GRAFANA_API_BASE_URL
datasource_url = grafana_url + 'api/ds/query'

# Headers, add your authentication here if needed
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + GRAFANA_SERVICE_ACCOUNT_BEARER_TOKEN
}


async def grafana_request(queries: list[str], steps_back: int = 0):
    # set the steps back concerning the number of results expected. For first iteration of train model the max amount
    # is set
    _steps_back = steps_back
    if steps_back == 0:
        _steps_back = 11000

    # create the default "from time" in epoch format where metric data will be fetched
    from_time_in_epochs = int(time.time() * 1000) - _steps_back * GRAFANA_INTERVAL_MS
    # create the default "to time" in epoch format that represents the present time till witch metric data will be
    # fetched
    to_time_in_epochs = int(time.time() * 1000)
    # array to keep the reference id of each query
    _ref_ids = []

    _data = {
        "queries": [],
        "from": str(from_time_in_epochs),
        "to": str(to_time_in_epochs)
    }
    for index, query in enumerate(queries):
        _ref_id = format_metric_string(query)
        _ref_ids.append(_ref_id)
        _data["queries"].append(
            {
                "refId": _ref_id,
                "expr": query,
                "range": True,
                "instant": False,
                "datasource": {
                    "type": "prometheus",
                    "uid": GRAFANA_DATASOURCE_UID
                },
                "editorMode": "code",
                "legendFormat": "__auto",
                "exemplar": False,
                "requestId": "1A",
                "utcOffsetSec": GRAFANA_UTC_OFFSET_SEC,
                "interval": "",
                "datasourceId": 1,
                "intervalMs": GRAFANA_INTERVAL_MS,
                "maxDataPoints": _steps_back
            }
        )

    # Send POST request
    response = requests.post(datasource_url, headers=headers, data=json.dumps(_data))

    # Check if request was successful
    if response.status_code == 200:
        # Process response here
        res = response.json()

        results = []
        # for each reference id that represents a response from Grafana create the results
        for _refId in _ref_ids:
            if len(res['results'][_refId]['frames'][0]['data']['values']) > 0:
                _results = []
                timestamps = res['results'][_refId]['frames'][0]['data']['values'][0]
                values = res['results'][_refId]['frames'][0]['data']['values'][1]
                for _index in range(len(timestamps)):
                    result = {'time': timestamps[_index], 'value': values[_index]}
                    _results.append(result)
                results.append({_refId: _results})
        return results
    else:
        logger.info('Failed to fetch data: {} {}'.format(response.status_code, response.text))
