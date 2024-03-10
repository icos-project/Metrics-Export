from prometheus_client import Gauge, Counter, Info
from metric_helpers import my_registry


def counter(existing_metric, metric_name, metric_info, labels, value):
    """
    Counters go up, and reset when the process restarts.

    :param existing_metric: The already existing metric if found
    :param metric_name: The metric name
    :param metric_info: The metric info
    :param labels: The labels that will pass for the metric
    :param value: The value of the counter
    :return: null
    """
    if metric_info is None:
        metric_info = metric_name + ' info'
    if labels:
        # Extract keys and store them in a list
        labels_keys = list(labels.keys())
    else:
        labels_keys = []

    if existing_metric is None:
        # Initialize a counter metric
        if labels_keys:
            c = Counter(metric_name, metric_info, labels_keys, registry=my_registry)
            # Increase the counter with labels from labels_dict and the value provided.
            c.labels(**labels).inc(value)
        else:
            c = Counter(metric_name, metric_info, [], registry=my_registry)
            c.inc(value)
        return c
    else:
        if labels_keys:
            # Increase the counter with labels from labels_dict and the value provided.
            existing_metric.labels(**labels).inc(value)
        else:
            existing_metric.inc(value)


def gauge(existing_metric, metric_name, metric_info, labels, value):
    """
    Gauges can go up and down.

    :param existing_metric: The already existing metric if found
    :param metric_name: The metric name
    :param metric_info: The metric info
    :param labels: The labels that will pass for the metric
    :param value: The value of the gauge
    :return: null
    """
    if metric_info is None:
        metric_info = metric_name + ' info'
    if labels:
        # Extract keys and store them in a list
        labels_keys = list(labels.keys())
    else:
        labels_keys = []
    # print(registry.__dict__)
    if existing_metric is None:
        # Initialize a gauge metric
        if labels_keys:
            g = Gauge(metric_name, metric_info, labels_keys, registry=my_registry)
            # Set the gauge with labels from labels_dict and the value provided.
            g.labels(**labels).set(value)
        else:
            g = Gauge(metric_name, metric_info, [], registry=my_registry)
            g.set(value)
        return g
    else:
        if labels_keys:
            # Set the gauge with labels from labels_dict and the value provided.
            existing_metric.labels(**labels).set(value)
        else:
            existing_metric.set(value)


def info(existing_metric, metric_name, metric_info, value):
    """
    Info tracks key-value information, usually about a whole target.

    :param existing_metric: The already existing metric if found
    :param metric_name: The metric name
    :param metric_info: The metric info
    :param value: The value of the info
    :return: null
    """
    if metric_info is None:
        metric_info = metric_name + ' info'

    if existing_metric is None:
        # Initialize an info metric
        i = Info(metric_name, metric_info, registry=my_registry)
        i.info(value)
        return i
    else:
        existing_metric.info(value)
