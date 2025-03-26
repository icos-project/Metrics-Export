# ICOS Metrics Export to Prometheus

## Introduction
This project provides a metrics export layer for ICOS, facilitating the monitoring and analysis of various 
metrics. Built on top of the `prometheus_client` library, it offers a lightweight and efficient way to 
expose metrics to Prometheus.

## Prerequisites
Before you start, ensure you have Python installed on your system (v3.11+). This project uses the 
`prometheus_client` library to expose metrics to Prometheus, so make sure to install it using pip:
```bash
pip install prometheus_client
```
or by installing all the requirements:
```bash
pip install -r requirements.txt
```

## Quick Start
To get started with the ICOS Metrics Export to Prometheus, simply run the ```src/main.py``` script. The script provides 
the below routes:

1) `/metrics`: This route will be used from Prometheus to scrape metrics. It exposes all the collected 
metrics in a format that Prometheus can understand and collect.

2) `/create_metric`: This route is used to create and update metrics, tailored to specific monitoring
   needs (type of metrics). It accepts a json payload that must contain:
    1) `metric_type` (mandatory): An **enum** that corresponds to the metric type:
        - Counter = 1
        - Gauge = 2
        - Info = 3
        - Enum = 4
    2) `metric_name`(mandatory): The name of the metric to be created or retrieved if it was already 
        created.
    3) `metric_info` (optional): The info of the metric to be created.
    4) `value` (mandatory): The value that will be passed to the metric.
    5) `labels` (optional): The dictionary of labels that will be set for the metric.
    6) `states` (optional): The list of states if an **Enum** metric is being set for the first time.

   After getting the properties it creates the specific metric asked and registers it to the internal 
   registry. **According to the metric type value**:
    - **Counter = 1**  
      Counter expects:
        - **metric_name (mandatory)** -> **str**. If there is a suffix of _total on the metric name, it will 
          be removed. When exposing the time series for counter, a _total suffix will be added. This is for 
          compatibility between OpenMetrics and the Prometheus text format, as OpenMetrics requires the 
          _total suffix.
        - **metric_info (optional)** -> **str | None**.
        - **value (mandatory)** -> **float**. The previous stored value will be incremented with that value. It 
          must be a positive number.
        - **labels (optional)** -> **Optional[Dict[str, str | int | float]]**.
        - states (ignored).
    - **Gauge = 2**  
      Gauge expects:
        - **metric_name (mandatory)** -> **str**.
        - **metric_info (optional)** -> **str | None**.
        - **value (mandatory)** -> **Union[float, str]**. It must be a parsable to float string. The new 
          value that will be set.
        - **labels (optional)** -> **Optional[Dict[str, str | int | float]]**.
        - states (ignored).
    - **Info = 3**  
      Info expects:
        - **metric_name (mandatory)** -> **str**.
        - **metric_info (optional)** -> **str | None**.
        - **value (mandatory)** -> **Dict[str, str | float]**. The new value that will be set.
        - **labels (optional)** -> **Optional[Dict[str, str | int | float]]**.
        - states (ignored),
    - **Enum = 4**  
      Enum expects:
        - **metric_name (mandatory)** -> **str**.
        - **metric_info (optional)** -> **str | None**.
        - **value (mandatory)** -> **str**. The state that will be set.
        - **labels (optional)** -> **Optional[Dict[str, str | int | float]]**.
        - **states (mandatory at creation of metric)**: The available choices of states that could be set.
          (passed only the first time)

3) `/unregister_metric`: This route can be used to delete/unregister a metric created. It accepts a json 
   payload that must contain:
   1) `metric_type` (mandatory): An **enum** that corresponds to the metric type:
      - Counter = 1
      - Gauge = 2
      - Info = 3
      - Enum = 4
   2) `metric_name` (mandatory) -> **str**: The name of the metric to be deleted/unregistered.

4) `/create_model_metric`: This route will receive a json payload to create a metric based on specific 
   telemetry data that will be retrieved from the Grafana instance of the cluster and a model that must 
   exist at Intelligence layer and will be inferred for predictions. The metric created will be 
   tailored to specific monitoring needs (type of metrics). It accepts a json payload that must contain:
    1) `metric_type` (mandatory): An **enum** that corresponds to the metric type:
        - Counter = 1
        - Gauge = 2
        - Info = 3
        - Enum = 4
    2) `metric_name`(mandatory): The name of the metric to be created or retrieved.
    3) `metric_info` (optional): The info of the metric to be created or retrieved.
    4) `labels` (optional): The dictionary of labels that will be set for the metric.
    5) `model_states` (optional): The list of states if an Enum metric is being set for the first time.
    6) `telemetry_metrics` (mandatory): The queries of the telemetry metrics from witch data will be retrieved.
    7) `model_tag` (mandatory): The name/tag of the model where the retrieved telemetry data will be sent.
    8) `step_in_seconds` (optional): The time distance between each sample at telemetry metric. Default is the 
       update rate of Prometheus.
    9) `steps_back` (mandatory): The amount of samples that will be used.
    10) `history_sample_size` (optional): TBD
    11) `data_interruption` (optional): TBD
    12) `history_data` (optional): TBD
  
   After getting the properties it creates the specific metric asked and registers it to the internal registry. 
   **According to the metric type value**:
    - **Counter = 1**  
      Counter expects:
        - **metric_name (mandatory)** -> **str**. If there is a suffix of _total on the metric name, it will be 
          removed. When exposing the time series for counter, a _total suffix will be added. This is for compatibility 
          between OpenMetrics and the Prometheus text format, as OpenMetrics requires the _total suffix.
        - **metric_info (optional)** -> **str | None**.
        - **labels (optional)** -> **Optional[Dict[str, str | int | float]]**.
        - model_states (ignored).
        - **telemetry_metrics (mandatory)** -> **list[str]**.
        - **model_tag (mandatory)** -> **str**.
        - **step_in_seconds (optional)** -> **int**.
        - **steps_back (mandatory)** -> **int**.
        - **history_sample_size (optional)** -> **int | None**.
        - **data_interruption (optional)** -> **bool = False**.
        - **history_data (optional)** -> **list[list[int]]**.
    - **Gauge = 2**  
      Gauge expects:
        - **metric_name (mandatory)** -> **str**.
        - **metric_info (optional)** -> **str | None**.
        - **labels (optional)** -> **Optional[Dict[str, str | int | float]]**.
        - model_states (ignored).
        - **telemetry_metrics (mandatory)** -> **list[str]**.
        - **model_tag (mandatory)** -> **str**.
        - **step_in_seconds (optional)** -> **int**.
        - **steps_back (mandatory)** -> **int**.
        - **history_sample_size (optional)** -> **int | None**.
        - **data_interruption (optional)** -> **bool = False**.
        - **history_data (optional)** -> **list[list[int]]**.
    - **Info = 3**  
      Info expects:
        - **metric_name (mandatory)** -> **str**.
        - **metric_info (optional)** -> **str | None**.
        - **labels (optional)** -> **Optional[Dict[str, str | int | float]]**.
        - model_states (ignored).
        - **telemetry_metrics (mandatory)** -> **list[str]**.
        - **model_tag (mandatory)** -> **str**.
        - **step_in_seconds (optional)** -> **int**.
        - **steps_back (mandatory)** -> **int**.
        - **history_sample_size (optional)** -> **int | None**.
        - **data_interruption (optional)** -> **bool = False**.
        - **history_data (optional)** -> **list[list[int]]**.
    - **Enum = 4**  
      Enum expects:
        - **metric_name (mandatory)** -> **str**.
        - **metric_info (optional)** -> **str | None**.
        - **value (mandatory)** -> **str**. The state that will be set.
        - **labels (optional)** -> **Optional[Dict[str, str | int | float]]**.
        - **model_states (mandatory at creation of metric)** -> **Optional[list[str]]**. The available states that will 
          be set (passed only the first time).
        - **telemetry_metrics (mandatory)** -> **list[str]**.
        - **model_tag (mandatory)** -> **str**.
        - **step_in_seconds (optional)** -> **int**.
        - **steps_back (mandatory)** -> **int**.
        - **history_sample_size (optional)** -> **int | None**.
        - **data_interruption (optional)** -> **bool = False**.
        - **history_data (optional)** -> **list[list[int]]**.

5) `stop_model_metrics` This route will receive a json payload to stop the metric creation(s) based on specific 
   telemetry data. The json passed will contain:
   1) `metric_names` (mandatory): A list of strings with the names of the metrics to be stopped.

6) `train_model_metric` This route will receive a json payload to start a model training based on specific telemetry 
   data that will be retrieved from the Grafana instance of the cluster. The json passed will contain:
   1) `labels` (optional) -> **Dict[str, str | int | float]**: The dictionary of labels that will be set for the metric.
   2) `model_name` (mandatory) -> **str**: The name of the model where the retrieved telemetry data will be sent.
   3) `model_type` (mandatory) -> **str**: The type of the model to be trained. Possible values: 
      - "XGB", 
      - "Arima".
   4) `test_size` (mandatory) -> **float**: A float number between 0 and 1 that will indicate the percentage of test data
      that will be used at training.
   5) `dataclay` -> **bool** : To use dataclay or not.
   6) `dataset_name` (optional) -> **str**: The name of the dataframe at Dataclay. If left empty new dataframe will be
      created from the result of Grafana queries.
   7) `steps_back` (mandatory) -> **int**: The amount of samples that will be used.
   8) `step_in_seconds` (optional) -> **int**: The time distance between each sample at telemetry metric. Default is the 
      update rate of Prometheus.
   9) `max_models_count` (optional) -> **int**: TBD
   10) `max_mlruns_count` (optional) -> **int**: TBD 
   11) `shap_samples` (optional) -> **int**: TBD 
   12) `model_parameters` (mandatory) -> **Dictionary**: The parameters needed based on the model type that will be 
       trained.  
      It must be a dictionary based on the model types:
        - **ArimaModelParameters**:
            - **p (optional)** -> **int**: TBD
            - **d (optional)** -> **int**: TBD
            - **q (optional)** -> **int**: TBD
        - **XGBModelParameters**:
            - **n_estimators (optional)** -> **int**: TBD
            - **max_depth (optional)** -> **int**: TBD
            - **eta (optional)** -> **float**: TBD
            - **subsample (optional)** -> **float**: TBD
            - **colsample_bytree (optional)** -> **float**: TBD
            - **alpha (optional)** -> **int**: TBD
   13) `telemetry_metrics` (mandatory) -> **list[str]**: A list of queries for telemetry metrics from witch data will be
      retrieved.

7) `show_models` This route will receive a json payload to show models that Intelligence API has stored to the model 
   registry. The json will contain:
   1) `model (optional)` -> **str = 'all'**: A string of the model(s) total to show.

## Usage
To start the metrics_generator either:
- create a docker image of it with the Dockerfile provided and deploy it.
- create a helm release from the helm provided at 'icos-export-custom-metrics-to-prometheus' folder.
- run it locally with
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```
- Metrics Export API uses Keycloack authentication of the cluster.
- the application needs to have the bellow environmental variables defined:  
    - `GRAFANA_API_BASE_URL`: The url which will be used to retrieve/query telemetry data.
    - `GRAFANA_SERVICE_ACCOUNT_BEARER_TOKEN`: The Bearer token that will be used for the Grafana queries. It is 
      automatically generated from the helm job.
    - `GRAFANA_INTERVAL_MS`: The seconds of the interval that Grafana gets informed from telemetry collectors 
      (Prometheus, Thanos).
    - `GRAFANA_UTC_OFFSET_SEC`: The UTC offset of the Grafana instance of the cluster.
    - `GRAFANA_DATASOURCE_UID`: The Datasource UUID that will be used at Grafana queries. It is automatically generated 
      from the helm job.
    - `INTELLIGENCE_API_BASE_URL`: The base url of the Intelligence API. It is automatically set from helm deployment.
    - `INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT`: The seconds of the interval repetition to predict new values for 
      create_model_metric.
    - `DATACLAY_HOST`: Dataclay's url.
    - `DATACLAY_USERNAME`: Dataclay's username. 
    - `DATACLAY_PASSWORD`: Dataclay's password. 
    - `KEYCLOAK_SERVER_URL`: Keycloak's url. It is automatically generated from the helm job.
    - `KEYCLOAK_REALM_NAME`: Keycloak's realm name. It is automatically generated from the helm job.
    - `KEYCLOAK_RESOURCE_SERVER_ID`: Keycloak's resource server id. It is automatically generated from the helm job.
    - `KEYCLOAK_AUDIENCE`: Keycloak's audience. It is automatically generated from the helm job.
    - `KEYCLOAK_CLIENT_ID`: Keycloak's client id. It is automatically generated from the helm job.
    - `KEYCLOAK_CLIENT_SECRET_KEY`: Keycloak's client secret key. It is automatically generated from the helm job. 
    - `AGGREGATOR_URL`: Aggregator's url. It is automatically generated from the helm job.

After the application is up, visiting `\docs` will show the swagger of the app.

## Contributing
Contributions to 'ICOS Metrics Export to Prometheus' are welcome. If you have suggestions for improvements or bug
fixes, please open an issue or submit a pull request.

# Legal
The ICOS Metrics Export to Prometheus is released under the Apache 2.0 license.
Copyright © 2022-2024 National and Kapodistrian University of Athens. All rights reserved.

🇪🇺 This work has received funding from the European Union's HORIZON research and innovation programme under grant 
agreement No. 101070177.
