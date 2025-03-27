from typing import Optional, Dict, Union, List

from prometheus_client import Gauge, Counter, Info, Enum
from prometheus_client.registry import Collector
from src.metric_helpers import my_registry, set_metric_info, set_label_keys


def counter(existing_metric: None | Collector, metric_name: str, metric_info: str | None,
            labels: Optional[Dict[str, str | int | float]], value: float):
    """
    Counters go up, and reset when the process restarts.

    If there is a suffix of _total on the metric name, it will be removed. When exposing the time series for counter,
    a _total suffix will be added. This is for compatibility between OpenMetrics and the Prometheus text format,
    as OpenMetrics requires the _total suffix.

    :param existing_metric: The already existing metric if found.
    :param metric_name: The metric name.
    :param metric_info: The metric info.
    :param labels: The labels that will be passed for the metric.
    :param value: The amount to increment the counter.

    :return: null.
    """
    # set metric info
    metric_info = set_metric_info(metric_name=metric_name, metric_info=metric_info)
    # if the metric does not exist, create it
    if existing_metric is None:
        # set label keys for the first creation of metric
        label_keys = set_label_keys(labels=labels)
        # Initialize a Counter metric
        if label_keys:
            c = Counter(name=metric_name, documentation=metric_info, labelnames=label_keys, registry=my_registry)
            c.labels(**labels).inc(amount=value)
        else:
            c = Counter(name=metric_name, documentation=metric_info, registry=my_registry)
            c.inc(amount=value)
    else:
        # Increase the Counter metric
        if labels:
            existing_metric.labels(**labels).inc(amount=value)
        else:
            existing_metric.inc(amount=value)


def gauge(existing_metric: None | Collector, metric_name: str, metric_info: str | None,
          labels: Optional[Dict[str, str | int | float]], value: Union[float, str]):
    """
    Gauges can go up and down.

    :param existing_metric: The already existing metric if found.
    :param metric_name: The metric name.
    :param metric_info: The metric info.
    :param labels: The labels that will be passed for the metric.
    :param value: The value to set the gauge. It must be a float or a parsable to float string.

    :return: null.
    """
    # set metric info
    metric_info = set_metric_info(metric_name=metric_name, metric_info=metric_info)
    # if the metric does not exist, create it
    if existing_metric is None:
        # set label keys for the first creation of metric
        label_keys = set_label_keys(labels=labels)
        # Initialize a Gauge metric
        if label_keys:
            g = Gauge(name=metric_name, documentation=metric_info, labelnames=label_keys, registry=my_registry)
            g.labels(**labels).set(value=value)
        else:
            g = Gauge(name=metric_name, documentation=metric_info, registry=my_registry)
            g.set(value)
    else:
        # Set the Gauge metric value
        if labels:
            existing_metric.labels(**labels).set(value=value)
        else:
            existing_metric.set(value=value)


def info(existing_metric: None | Collector, metric_name: str, metric_info: str | None,
         labels: Optional[Dict[str, str | int | float]], value: Dict[str, str | float]):
    """
    Info tracks key-value information, usually about a whole target.

    :param existing_metric: The already existing metric if found.
    :param metric_name: The metric name.
    :param metric_info: The metric info.
    :param labels: The labels that will be passed for the metric.
    :param value: The key-value information dictionary of the info.

    :return: null.
    """
    # set metric info
    metric_info = set_metric_info(metric_name=metric_name, metric_info=metric_info)
    # make all value properties strings
    for value_key in value.keys():
        value[value_key] = str(value[value_key])
    # if the metric does not exist, create it
    if existing_metric is None:
        # set label keys for the first creation of metric
        label_keys = set_label_keys(labels=labels)
        # Initialize an Info metric
        if label_keys:
            i = Info(name=metric_name, documentation=metric_info, labelnames=label_keys, registry=my_registry)
            i.labels(**labels).info(val=value)
        else:
            i = Info(name=metric_name, documentation=metric_info, registry=my_registry)
            i.info(val=value)
    else:
        # clear labels from already passed value keys
        if labels:
            for value_key in value.keys():
                labels.pop(value_key, None)
        # Set the Info metric value
        if labels:
            existing_metric.labels(**labels).info(val=value)
        else:
            existing_metric.info(val=value)


def enum(existing_metric: None | Collector, metric_name: str, metric_info: str | None,
         labels: Optional[Dict[str, str | int | float]], states: List[str], state: str):
    """
    Enum tracks which of a set of states something is currently in.

    :param existing_metric: The already existing metric if found.
    :param metric_name: The metric name.
    :param metric_info: The metric info.
    :param labels: The labels that will be passed for the metric.
    :param states: The states that will be available for the metric at its creation.
    :param state: The state to be set.

    :return: null.
    """
    # if state passed does not exist in states passed (at creation/update) return Value Error
    if state not in states:
        raise ValueError('state not in states.')
    # set metric info
    metric_info = set_metric_info(metric_name=metric_name, metric_info=metric_info)
    # if the metric does not exist, create it
    if existing_metric is None:
        # set label keys for the first creation of metric
        label_keys = set_label_keys(labels=labels)
        # Initialize an Enum metric
        if label_keys:
            e = Enum(name=metric_name, documentation=metric_info, labelnames=label_keys, states=states,
                     registry=my_registry)
            e.labels(**labels).state(state=state)
        else:
            e = Enum(name=metric_name, documentation=metric_info, states=states, registry=my_registry)
            e.state(state=state)
    else:
        # need to pop the label with metric name as ".state(...)" sets it again
        labels.pop(metric_name, None)
        if labels:
            existing_metric.labels(**labels).state(state=state)
        else:
            existing_metric.state(state=state)
