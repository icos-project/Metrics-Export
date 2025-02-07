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
    logger.info('headers: {}'.format(headers))
    logger.info('data: {}'.format(json.dumps(_data)))
    response = requests.post(datasource_url, headers=headers, data=json.dumps(_data))

    # Check if request was successful
    logger.info('response.status_code: {}'.format(response.status_code))
    if response.status_code == 200:
        # Process response here
        res = response.json()

        results = []
        # for each reference id that represents an response from Grafana create the results
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


# def find_csv_files(starts_with):
#     return [file for file in os.listdir(DIRECTORY)
#             if file.endswith('.csv') and file.startswith(starts_with)]
#
#
# if __name__ == '__main__':
#     # if len(sys.argv) > 2:
#     # CSV_FILE_NAMES = json.loads(sys.argv[1])
#     # print(f"Argument 1: {CSV_FILE_NAMES}")
#     # DIRECTORY = sys.argv[2]
#     # print(f"Argument 2: {DIRECTORY}")
#     CSV_FILE_NAMES = ['icos_crud_tests']
#     DIRECTORY = 'C:\\Users\\Da-Wi\\OneDrive\\Desktop\\dataServers'
#
#     for CSV_FILE_NAME in CSV_FILE_NAMES:
#         icos_tests_csv_files = find_csv_files(CSV_FILE_NAME)
#
#         master_df = pd.DataFrame()
#         for index, _file in enumerate(icos_tests_csv_files):
#             print("{} - {}".format(index + 1, len(icos_tests_csv_files)))
#             dataset_model_params = pd.read_csv(DIRECTORY + '/' + _file)
#
#             # Remove items that match 'start_time', 'end_time' and 'containerId'
#             excluded_values = ["start_time", "end_time", "containerId"]
#             columns_list = [item for item in dataset_model_params.columns.tolist() if item not in excluded_values]
#
#             for index, dataset_model_params_row in dataset_model_params.iterrows():
#                 start_time = str(dataset_model_params_row['start_time'])
#                 end_time = str(dataset_model_params_row['end_time'])
#                 container_id = str(dataset_model_params_row['containerId'])
#                 consumptions = grafana_request(_container_id=container_id, _from=start_time, _to=end_time)
#                 if consumptions is not None:
#                     for i in range(len(consumptions)):
#                         data = {}
#                         for column in columns_list:
#                             data[str(column)] = dataset_model_params_row[str(column)]
#                         data['time'] = consumptions[i]['time'],
#                         data['consumption'] = consumptions[i]['consumption']
#                         data_df = pd.DataFrame(data)
#                         master_df = pd.concat([master_df, data_df], ignore_index=True)
#
#         if len(master_df.columns) > 0:
#             print('columns: ', master_df.columns)
#             if CSV_FILE_NAME.startswith('icos_crud_tests'):
#                 convert_dict = {
#                     'parallelInstancesNumber': int,
#                     'time': float64,
#                     'consumption': float64
#                 }
#             if CSV_FILE_NAME.startswith('icos_lstm_tests'):
#                 convert_dict = {
#                     'hidden_layers': int,
#                     'sequence_size': int,
#                     'batch_size': int,
#                     'time': float64,
#                     'consumption': float64
#                 }
#             if CSV_FILE_NAME.startswith('icos_imageProcessing_tests'):
#                 convert_dict = {
#                     'img_analysis': int,
#                     'time': float64,
#                     'consumption': float64
#                 }
#
#             sorting_values = columns_list
#             sorting_values.append('time')
#             master_df = master_df.astype(convert_dict)
#             master_df = master_df.sort_values(by=sorting_values)
#
#             results_directory = os.path.join(DIRECTORY, 'results')
#             # Check if the directory exists
#             if not os.path.exists(results_directory):
#                 # Create the directory, including any necessary intermediate directories
#                 os.makedirs(results_directory)
#                 print(f"Directory '{results_directory}' was created.")
#             else:
#                 print(f"Directory '{results_directory}' already exists.")
#
#             results_file = os.path.join(results_directory, 'results_{}.csv'.format(CSV_FILE_NAME))
#             if os.path.exists(results_file):
#                 print("File exists.")
#                 master_df.to_csv(results_file, index=False, mode='a', header=False)
#             else:
#                 print("File does not exist.")
#                 master_df.to_csv(results_file, index=False, mode='w')
#
# #     sys.exit(200)
# # else:
# #     print("No arguments were passed.")
