from prometheus_client import CollectorRegistry
from enum import Enum
from pydantic import BaseModel
from typing import Union, Dict, Optional

from src.environment_variables import INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT

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


# create the enums of model types
class ModelType(Enum):
    XGB = 'XGB'
    Arima = 'Arima'


class MetricItemRequest(BaseModel):
    metric_type: MetricType
    metric_name: str
    metric_info: Optional[str] = None
    value: Union[float, str, dict[str, str | float]]
    labels: Optional[Dict[str, str | int | float]] = {}
    states: Optional[list[str]] = []


class UnregisterMetricItemRequest(BaseModel):
    metric_type: MetricType
    metric_name: str


class CreateModelMetricItemRequest(BaseModel):
    metric_type: MetricType
    metric_name: str
    metric_info: Optional[str] = None
    labels: Optional[Dict[str, str | int | float]] = {}
    telemetry_metrics: list[str]
    model_tag: str
    model_states: Optional[list[str]] = []
    step_in_seconds: Optional[int] = INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT
    steps_back: int
    history_sample_size: Optional[int] = None
    data_interruption: bool = False
    history_data: Optional[list[list[int]]] = [[]]


class StopModelMetricItemRequest(BaseModel):
    metric_names: list[str]


# create the types for Arima model parameters
class ArimaModelParameters(BaseModel):
    p: Optional[int] = None
    d: Optional[int] = None
    q: Optional[int] = None


class ArimaModel(BaseModel):
    xgboost_model_parameters: ArimaModelParameters


# create the types for XGB model parameters
class XGBModelParameters(BaseModel):
    n_estimators: Optional[int] = None
    max_depth: Optional[int] = None
    eta: Optional[float] = None
    subsample: Optional[float] = None
    colsample_bytree: Optional[float] = None
    alpha: Optional[int] = None


class XGBModel(BaseModel):
    xgboost_model_parameters: XGBModelParameters


# create the types for PyTorch model parameters
class PyTorchModelParameters(BaseModel):
    hidden_size: Optional[int] = None
    num_epochs: Optional[int] = None
    quantize: Optional[bool] = None
    distill: Optional[bool] = None


class PyTorchModel(BaseModel):
    pytorch_model_parameters: PyTorchModelParameters


class TrainModelMetricItemRequest(BaseModel):
    labels: Optional[Dict[str, str | int | float]] = {}
    model_name: str
    model_type: ModelType
    test_size: float
    dataclay: bool = False
    dataset_name: str | None = None
    steps_back: int
    step_in_seconds: Optional[int] = INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT
    max_models_count: Optional[int] = None
    max_mlruns_count: Optional[int] = None
    shap_samples: Optional[int] = None
    model_parameters: ArimaModel | XGBModel | PyTorchModel
    telemetry_metrics: list[str]


class ShowModelsRequest(BaseModel):
    model: str = 'all'

