import logging
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Union, Dict, Optional
from fastapi import FastAPI, HTTPException
from prometheus_client import make_asgi_app
from prometheus_client.multiprocess import MultiProcessCollector
from prometheus_client.registry import Collector
from metric_helpers import my_registry
from metric_types_functions import counter, gauge, info


# Using multiprocess collector for registry
def make_metrics_app(custom_registry):
    MultiProcessCollector(custom_registry)
    return make_asgi_app(registry=custom_registry)


# Create app
app = FastAPI(debug=False)
# set a typical logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Initialize the custom registry
registry = my_registry
# Add prometheus asgi middleware to route /metrics requests
metrics_app = make_asgi_app(registry)
app.mount("/metrics", metrics_app)


# create the enums of metric types
class MetricType(Enum):
    Counter = 1
    Gauge = 2
    Summary = 3
    Histogram = 4
    Info = 5
    Enum = 6
    Exemplars = 7


class MetricItemRequest(BaseModel):
    type: MetricType
    metric_name: str
    metric_info: Optional[str] = None
    value: Union[float, str]
    labels: Optional[Dict[str, str]] = {}


class ResetCounterItemRequest(BaseModel):
    metric_name: str


# Function to get an existing metric by name from the registry
def get_metric_by_name_and_type(metric_name: str, metric_type: MetricType) -> None | Collector:
    """
    Retrieves the metric that was registered with the given name.

    :param metric_name: The name of the metric that must be found.
    :param metric_type: The type of the metric to check that a metric with the same name but different type exists.
    :return: The metric that was found else None
    """
    for collector in registry._collector_to_names.keys():
        # Check if this collector is the one we're looking for based on its name
        if metric_name in registry._collector_to_names[collector]:
            collector_type = type(collector).__name__.lower()
            metric_type = metric_type.name.lower()
            if collector_type != metric_type:

                raise HTTPException(status_code=400,
                                    detail='Metric name matches an already registered metric with different type.')
            return collector
    return None


# Get the labels that were set at the first registration of a metric
def get_existing_metric_labels(metric: Collector) -> dict[str, str] | None:
    """
    Retrieve the labels of an existing metric.

    :param metric: The metric as a Collector. Extract from it the type and actual name.
    :return: The labels registered as a dictionary or None
    """
    # Assuming `metric` is a Prometheus metric object, like an instance of prometheus_client.Gauge
    metric_type = type(metric).__name__.lower()
    metric_name = metric._name
    for metric_registered in registry.collect():
        if metric_registered.type == metric_type:
            for sample in metric_registered.samples:
                if metric_type == 'counter':
                    metric_name = metric_name + '_total'
                if sample.name == metric_name:
                    return sample.labels
    return None


def get_full_labels_set(metric_name: Collector, request_labels: dict[str, str] | None) -> dict[str, str] | None:
    """
    Will check if the labels passed at the request are aligned with the labels the metric expects.
    If any label is missing, then set it with empty string "".
    If labels do not match then throw error.

    :param metric_name: The name of the metric.
    :param request_labels: The labels that have been passed at request.
    :return: New dictionary with labels and their values.
    """
    metric_preset_labels = get_existing_metric_labels(metric_name)
    # Check if the request has only a part of the labels
    new_labels = request_labels
    for label in metric_preset_labels:
        if label not in new_labels:
            new_labels[label] = ""  # Set missing label to ""

    # If the request has more or different labels than when the metric was registered
    if not all(label in metric_preset_labels for label in new_labels):
        raise HTTPException(status_code=400,
                            detail='Request contains more or different labels than the registered metric')
    else:
        return new_labels


@app.get("/")
def read_root():
    return


@app.post('/create_metric')
def create_metric(request: MetricItemRequest):
    """
    create_metric route will receive a json payload to create or update a metric.

    :param request: The json passed will contain:
    - type (mandatory): The metric type:
        - Counter = 1
        - Gauge = 2
        - Summary = 3
        - Histogram = 4
        - Info = 5
        - Enum = 6
        - Exemplars = 7
    - metric_name (mandatory): The name of the metric to be created or retrieved.
    - metric_info (optional): The info of the metric to be created or retrieved.
    - value (mandatory): The value that will be passed to the metric.
    - labels (optional): The dictionary of labels that will be set for the metric.
    :return: a json response with 400 if error occurs or 200 if metric is saved successfully.
    """
    # get the metrics type value.
    metric_type = request.type
    # get the metric name
    # Strip whitespace and check if it's not None or empty
    metric_name = request.metric_name.strip() if request.metric_name else None
    # get metric info
    metric_info = request.metric_info
    # get the value passed
    value = request.value
    # get metric labels
    labels = request.labels

    # if metric name is not passed then return error
    if not metric_name:
        logger.error('metric_name not passed.')
        raise HTTPException(status_code=400, detail='metric_name is required.')

    # if value is not passed then return error
    if isinstance(value, str):
        # If value is a string, strip whitespace and check if it's empty
        if not value.strip():
            logger.error('value as str is required and cannot be empty or just whitespace.')
            raise HTTPException(status_code=400,
                                detail='value as str is required and cannot be empty or just whitespace.')
    elif value is None:  # Explicitly check for None if it's not a string (assuming float)
        logger.error('value as float is required and cannot be None.')
        raise HTTPException(status_code=400, detail='value as float is required and cannot be None.')

    # check if metric already exists and has the same type
    # if it already exists then just update it at the metric runs
    try:
        existing_metric = get_metric_by_name_and_type(metric_name, metric_type)
    except HTTPException as http_exc:
        # Log the exception or do additional processing
        logger.error('HTTPException: {}'.format(http_exc.detail))
        # Re-raise the HTTPException for FastAPI to handle
        raise http_exc

    # check that the labels passed for calling an existing metric are correct
    try:
        if existing_metric is not None:
            labels = get_full_labels_set(existing_metric, labels)
    except HTTPException as http_exc:
        # Log the exception or do additional processing
        logger.error('HTTPException: {}'.format(http_exc.detail))
        # Re-raise the HTTPException for FastAPI to handle
        raise http_exc

    try:
        # Update the appropriate metric based on the enum
        if metric_type == MetricType.Counter:
            counter(existing_metric, metric_name, metric_info, labels, value)
        elif metric_type == MetricType.Gauge:
            gauge(existing_metric, metric_name, metric_info, labels, value)
        elif metric_type == MetricType.Summary:
            raise HTTPException(status_code=500, detail='Not implemented yet.')
        elif metric_type == MetricType.Histogram:
            raise HTTPException(status_code=500, detail='Not implemented yet.')
        elif metric_type == MetricType.Info:
            raise HTTPException(status_code=500, detail='Not implemented yet.')
            # metric = info(existing_metric, metric_name, metric_info, value)
        elif metric_type == MetricType.Enum:
            raise HTTPException(status_code=500, detail='Not implemented yet.')
        elif metric_type == MetricType.Exemplars:
            raise HTTPException(status_code=500, detail='Not implemented yet.')
    except ValueError as e:
        # Log the exception
        logger.error('HTTPException: {}'.format(e))
        # Raise the HTTPException for FastAPI to handle
        raise HTTPException(status_code=400, detail='{}'.format(e))

    logger.info('Time: {}, metrics name: {}, value: {}'.format(
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], metric_name, value))

    return {'message': 'Metric updated successfully.'}


# reset counters that have been created
@app.post('/unregister_metric')
def reset_counter(request: ResetCounterItemRequest):
    """
    unregister_metric route will receive a json payload to unregister a metric.

    :param request: The json passed will contain:
    - metric_name (mandatory): The name of the metric to be unregistered.
    :return: a json response with 200 if metric is unregistered successfully.
    """
    # check if counter metric already exists and has the same type
    # if it already exists then reset it
    try:
        existing_counter_metric = get_metric_by_name_and_type(request.metric_name, MetricType.Gauge)
        if existing_counter_metric is not None:
            registry.unregister(existing_counter_metric)
            return {'message': 'Unregistered metric successfully.'}
        return {'message': 'Metric not found. You can create a new one.'}
    except HTTPException as http_exc:
        # Log the exception or do additional processing
        logger.error('HTTPException: {}'.format(http_exc.detail))
        # Re-raise the HTTPException for FastAPI to handle
        raise http_exc
