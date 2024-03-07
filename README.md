# ICOS Intelligence Layer Metrics Export

## Introduction
This project provides a metrics export layer for ICOS intelligence, facilitating the monitoring and analysis of various 
metrics. Built on top of the `prometheus_client` library, it offers a lightweight and efficient way to expose metrics to
Prometheus.

## Prerequisites
Before you start, ensure you have Python installed on your system. This project uses the `prometheus_client` library to 
expose metrics to Prometheus, so make sure to install it using pip:

```bash
pip install prometheus_client
```

## Quick Start
To get started with the ICOS Intelligence Layer Metrics Export, simply run the metrics_generator.py script. The script 
provides two routes for metrics exposure:

1) /metrics: This route will be used from Prometheus to scrape metrics. It exposes all the collected metrics in a format 
that Prometheus can understand and collect.

2) /process_model: This route can be configured to accept metrics of specific models, tailored to specific monitoring 
needs. It accepts a json payload with a model and a result property:
   1) `model` property is the name of the model.
   2) `result` property is the value of the model prediction. 

After getting the properties it creates a gauge metric that has as a property the model name and as a value the
result value. 

## Usage
```bash
python metrics_generator.py
```
This command will start the metrics export layer, making it accessible to Prometheus via the defined routes.

## Contributing
Contributions to the ICOS Intelligence Layer Metrics Export are welcome. If you have suggestions for improvements or bug
fixes, please open an issue or submit a pull request.

# ICOS Metrics Export 

# Legal
The ICOS Metrics Export  is released under the {LICENSE NAME} license.
Copyright © 2022-2024 National and Kapodistrian University of Athens. All rights reserved.

🇪🇺 This work has received funding from the European Union's HORIZON research and innovation programme under grant agreement No. 101070177.
