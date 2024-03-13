# ICOS Metrics Export to Prometheus

## Introduction
This project provides a metrics export layer for ICOS, facilitating the monitoring and analysis of various 
metrics. Built on top of the `prometheus_client` library, it offers a lightweight and efficient way to expose metrics to
Prometheus.

## Prerequisites
Before you start, ensure you have Python installed on your system. This project uses the `prometheus_client` library to 
expose metrics to Prometheus, so make sure to install it using pip:

```bash
pip install prometheus_client
```

## Quick Start
To get started with the ICOS Metrics Export to Prometheus, simply run the metrics_generator.py script. The script 
provides three routes for metrics exposure and removal:

1) `/metrics`: This route will be used from Prometheus to scrape metrics. It exposes all the collected metrics in a format 
that Prometheus can understand and collect.

2) `/unregister_metric`: This route can be used to delete/unregister a metric created. It accepts a json payload that must contain:
   1) `metric_name` (mandatory): The name of the metric to be deleted/unregistered.

3) `/create_metric`: This route can be configured to create and update metrics, tailored to specific monitoring 
needs (type of metrics). It accepts a json payload that must may contain:
   1) `type` (mandatory): The metric type:
      - Counter = 1
      - Gauge = 2
      - Info = 3
      - Enum = 4
   2) `metric_name`(mandatory): The name of the metric to be created or retrieved.
   3) `metric_info` (optional): The info of the metric to be created or retrieved.
   4) `value` (mandatory): The value that will be passed to the metric.
   5) `labels` (optional): The dictionary of labels that will be set for the metric.
   6) `states` (optional): The list of states if an Enum metric is being set for the first time.

   After getting the properties it creates the specific metric asked and registers it to the internal registry. According to the metric type value:
   - Counter = 1  
   Counter expects: 
     - metric_name (mandatory) -> string. If there is a suffix of _total on the metric name, it will be removed.
     When exposing the time series for counter, a _total suffix will be added. This is for compatibility between
     OpenMetrics and the Prometheus text format, as OpenMetrics requires the _total suffix.
     - metric_info (optional) -> string | None.
     - value (mandatory): the previous stored value will be incremented with that value -> positive number.
     - labels (optional) -> Optional[Dict[str, str | int | float]].
     - states (ignored).
   - Gauge = 2  
   Gauge expects:
     - metric_name (mandatory) -> string.
     - metric_info (optional) -> string | None.
     - value (mandatory): the new value that will be set -> Union[float, str] (must be a parsable to float
     string.).
     - labels (optional) -> Optional[Dict[str, str | int | float]].
     - states (ignored).
   - Info = 3  
   Info expects:
     - metric_name (mandatory) -> string.
     - metric_info (optional) -> string | None.
     - value (mandatory): the new value that will be set -> Dict[str, str | float].
     - labels (optional) -> Optional[Dict[str, str | int | float]].
     - states (ignored),
   - Enum = 4
   Enum expects:
     - metric_name (mandatory) -> string.
     - metric_info (optional) -> string | None.
     - value (mandatory): the state that will be set.
     - labels (optional) -> Optional[Dict[str, str | int | float]].
     - states (mandatory at creation of metric): the states that will be the available choice to set the state
     (passed only the first time)

## Usage
To start the metrics_generator either:
- create a docker image of it with the Dockerfile provided and deploy it.
- create a helm release from the helm provided at 'icos-export-custom-metrics-to-prometheus' folder.
- run it locally with
   ```bash
   uvicorn metrics_generator:app --reload --host 0.0.0.0 --port 8000
   ```

After the application is up, visiting `\doc` will show the swagger of the app.

## Contributing
Contributions to 'ICOS Metrics Export to Prometheus' are welcome. If you have suggestions for improvements or bug
fixes, please open an issue or submit a pull request.

# Legal
The ICOS Metrics Export to Prometheus is released under the Apache 2.0 license.
Copyright © 2022-2024 National and Kapodistrian University of Athens. All rights reserved.

🇪🇺 This work has received funding from the European Union's HORIZON research and innovation programme under grant agreement No. 101070177.
