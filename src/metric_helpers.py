from prometheus_client import CollectorRegistry
from enum import Enum
from pydantic import BaseModel
from typing import Union, Dict, Optional

# Initialize the custom registry
my_registry = CollectorRegistry()


def set_metric_info(metric_name: str, metric_info: str | None) -> str:
    if metric_info is None:
        metric_info = metric_name + ' info'
    return metric_info


def set_label_keys(labels: Dict[str, str | int | float] | None) -> list[str]:
    # if labels exist, create the label keys
    if labels:
        # Extract keys and store them in a list
        labels_keys = list(labels.keys())
    else:
        labels_keys = []
    return labels_keys


# create the enums of metric types
class MetricType(Enum):
    Counter = 1
    Gauge = 2
    Info = 3
    Enum = 4


class MetricItemRequest(BaseModel):
    type: MetricType
    metric_name: str
    metric_info: Optional[str] = None
    value: Union[float, str, dict[str, str | float]]
    labels: Optional[Dict[str, str | int | float]] = {}
    states: Optional[list[str]] = []


class UnregisterMetricItemRequest(BaseModel):
    metric_name: str


class CreateModelMetricItemRequest(BaseModel):
    type: MetricType
    metric_name: str
    metric_info: Optional[str] = None
    labels: Optional[Dict[str, str | int | float]] = {}
    states: Optional[list[str]] = []
    telemetry_metric: str
    model_route: str
    model_name: str
    model_type: str
    step_in_seconds: int
    sequence_size: int


class StopModelMetricItemRequest(BaseModel):
    metric_names: list[str]
