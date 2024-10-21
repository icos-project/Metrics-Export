import asyncio
import logging
import time
import threading
from datetime import datetime
from fastapi import FastAPI, HTTPException
from prometheus_client import make_asgi_app
from prometheus_client.multiprocess import MultiProcessCollector
from prometheus_client.registry import Collector

from src.dataclay_dataframe_store import create_and_save_dataframe_to_dataclay
from src.grafana_request import grafana_request
from src.metric_helpers import my_registry, MetricType, MetricItemRequest, UnregisterMetricItemRequest, \
    TrainModelMetricItemRequest, CreateModelMetricItemRequest, StopModelMetricItemRequest
from src.metric_types_functions import counter, gauge, info, enum
from src.intelligence_layer import call_intelligence_api_infer_model, prepare_results_for_model_input, \
    call_intelligence_api_train_model
from src.environment_variables import INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT


# Using multiprocess collector for registry
def make_metrics_app(custom_registry):
    MultiProcessCollector(custom_registry)
    return make_asgi_app(registry=custom_registry)


# Create app
app = FastAPI(debug=False)
# set a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Initialize the custom registry
registry = my_registry
# Add prometheus asgi middleware to route /metrics requests
metrics_app = make_asgi_app(registry)
app.mount("/metrics", metrics_app)
# Global dictionary to store threads and stop events
threads = {}
stop_events = {}


# Function to get an existing metric by name from the registry
def get_metric_by_name_and_type(metric_name: str, metric_type: MetricType) -> None | Collector:
    """
    Retrieves the metric that was registered with the given name.

    :param metric_name: The name of the metric that must be found.
    :param metric_type: The type of the metric to check in order to avoid the possibility that a metric with the same
    name but different type exists.

    :return: The metric that was found else None
    """
    for collector in registry._collector_to_names.keys():
        # Check if this collector is the one we're looking for based on its name
        if metric_name in registry._collector_to_names[collector]:
            collector_type = type(collector).__name__.lower()
            metric_type = metric_type.name.lower()
            if collector_type != metric_type:
                http_err = 'Metric name matches an already registered metric with different type.'
                logger.error(http_err)
                raise HTTPException(status_code=400, detail=http_err)
            return collector
    return None


# Get the labels that were set at the first registration of a metric
def get_existing_metric_labels(metric: Collector) -> dict[str, str] | None:
    """
    Retrieve the labels of an existing metric.

    :param metric: The metric as a Collector. Extract from it the type and actual name.

    :return: The labels registered as a dictionary or None
    """
    # Assuming `metric` is a Prometheus metric object
    metric_name = metric._name
    metric_type = type(metric).__name__.lower()
    # adjust metric name for a Counter metric
    if metric_type == 'counter':
        metric_name = metric_name + '_total'
    # adjust metric name for an Info metric
    if metric_type == 'info':
        metric_name = metric_name + '_info'
    # adjust Enum metric type (it is 'stateset')
    if metric_type == 'enum':
        metric_type = 'stateset'
    for metric_registered in registry.collect():
        if metric_registered.type == metric_type:
            for sample in metric_registered.samples:
                if sample.name == metric_name:
                    return sample.labels
    return None


def get_full_labels_set(metric_name: Collector, request_labels: dict[str, str] | None) -> dict[str, str] | None:
    """
    Will check if the labels passed at the request are aligned with the labels the metric expects.
    If any label is missing, then set it with empty string ''.
    If labels do not match then throw error.

    :param metric_name: The name of the metric.
    :param request_labels: The labels that have been passed at request.

    :return: New dictionary with labels and their values or None.
    """
    metric_preset_labels = get_existing_metric_labels(metric_name)
    if metric_preset_labels:
        # Check if the request has only a part of the labels
        new_labels = request_labels
        for label in metric_preset_labels:
            if label not in new_labels:
                # Set missing label to ''
                new_labels[label] = ''
        # If the request has more or different labels than when the metric was registered
        if not all(label in metric_preset_labels for label in new_labels):
            http_err = 'Request contains more or different labels than the registered metric.'
            logger.error(http_err)
            raise HTTPException(status_code=400, detail=http_err)
        else:
            return new_labels
    else:
        return None


@app.get("/")
def read_root():
    return


@app.post('/create_metric')
def create_metric(request: MetricItemRequest):
    """
    create_metric route will receive a json payload to create or update a metric.

    :param request: The json passed will contain:

    - metric_type (mandatory): The metric type.
    - metric_name (mandatory): The name of the metric to be created or retrieved.
    - metric_info (optional): The info of the metric to be created or retrieved.
    - value (mandatory): The value that will be passed to the metric.
    - labels (optional): The dictionary of labels that will be set for the metric.
    - states (optional): The list of states if an enum metric is being set for the first time.

    According to the metric type value:

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

    :return: a json response with 400 if error occurs or 200 if metric is saved successfully.
    """
    # get the metrics type value
    metric_type = request.metric_type
    # get the metric name. Strip whitespace and check if it's not None or empty
    metric_name = request.metric_name.strip() if request.metric_name else None
    # get metric info
    metric_info = request.metric_info
    # get the value passed
    value = request.value
    # get metric labels
    labels = request.labels
    # get states
    states = request.states

    # if metric name is not passed then return error
    if not metric_name:
        http_err = 'metric_name is required.'
        logger.error(http_err)
        raise HTTPException(status_code=400, detail=http_err)

    # if value is not passed then return error
    if isinstance(value, str):
        if not value.strip():
            # If value is a string, strip whitespace and check if it's empty
            http_err = 'value as str is required and cannot be empty or just whitespace.'
            logger.error(http_err)
            raise HTTPException(status_code=400, detail=http_err)
    elif value is None:  # Explicitly check for None if it's not a string (assuming float)
        http_err = 'value as float is required and cannot be None.'
        logger.error(http_err)
        raise HTTPException(status_code=400, detail=http_err)

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
            counter(existing_metric=existing_metric, metric_name=metric_name, metric_info=metric_info, labels=labels,
                    value=value)
        elif metric_type == MetricType.Gauge:
            gauge(existing_metric=existing_metric, metric_name=metric_name, metric_info=metric_info, labels=labels,
                  value=value)
        elif metric_type == MetricType.Info:
            if not isinstance(value, dict):
                http_err = 'value at info metric must be a dictionary.'
                logger.error(http_err)
                raise HTTPException(status_code=400, detail=http_err)
            info(existing_metric=existing_metric, metric_name=metric_name, metric_info=metric_info, labels=labels,
                 value=value)
        elif metric_type == MetricType.Enum:
            enum(existing_metric=existing_metric, metric_name=metric_name, metric_info=metric_info, labels=labels,
                 states=states, state=value)
    except ValueError as e:
        # Log the exception
        logger.error('HTTPException: {}'.format(e))
        # Raise the HTTPException for FastAPI to handle
        raise HTTPException(status_code=400, detail='{}'.format(e))

    logger.info('Time: {}, metrics name: {}, value: {}'.format(
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], metric_name, value))

    return {'message': 'Metric updated successfully.'}


# unregister metrics that have been created
@app.post('/unregister_metric')
def unregister_metric(request: UnregisterMetricItemRequest):
    """
    unregister_metric route will receive a json payload to unregister a metric.

    :param request: The json passed will contain:

    - metric_type (mandatory) -> MetricType(Enum) : The metric type.
    - metric_name (mandatory) -> string : The name of the metric to be unregistered.

    :return: a json response (200) if metric is unregistered successfully.
    """
    # check if counter metric already exists and has the same type
    # if it already exists then reset it
    try:
        existing_counter_metric = get_metric_by_name_and_type(request.metric_name, request.metric_type)
        if existing_counter_metric is not None:
            registry.unregister(existing_counter_metric)
            return {'message': 'Unregistered metric successfully.'}
        return {'message': 'Metric not found. You can create a new one.'}
    except HTTPException as http_exc:
        # Log the exception or do additional processing
        logger.error('HTTPException: {}'.format(http_exc.detail))
        # Re-raise the HTTPException for FastAPI to handle
        raise http_exc


async def repeated_operation(request: CreateModelMetricItemRequest, exception_list):
    """
    The whole operation that will run repeatedly to get data from Grafana, call an intelligence api model and
    post the metric.

    :param request: The request contains all the info needed (model name, query, sequence size, steps etc.).
    :param exception_list: A list to store exceptions.

    :return: None
    """
    steps_back = request.steps_back
    try:
        # step 1 --> using the service account at Grafana create the queries based on the telemetry metrics asked
        grafana_results = await grafana_request(request.telemetry_metrics, steps_back)

        if grafana_results is not None and len(grafana_results) > 0:
            # prepare the input data for the model
            model_input_data = prepare_results_for_model_input(grafana_results, steps_back)
            # run the model and save the result
            model_result_status_code, model_result = call_intelligence_api_infer_model(request, model_input_data)
            # If model_result_status_code is not 200, exception must be thrown for error with intelligence API
            # communication
            if model_result_status_code != 200:
                http_err = 'Intelligence API error or endpoint does not exist.'
                raise HTTPException(status_code=400, detail=http_err)
            model_result = model_result[0][0]
            # post the result
            data = request.dict(include={
                'metric_type',
                'metric_name',
                'metric_info',
                'labels'
            })
            data['states'] = request.model_states
            data['value'] = model_result
            create_metric(MetricItemRequest(**data))
        else:
            # If result is None, exception must be thrown for empty data
            http_err = 'Telemetry metric not found or returned null results.'
            raise HTTPException(status_code=400, detail=http_err)
    except Exception as e:
        exception_list.append(e)


async def create_model_telemetry_metric(request: CreateModelMetricItemRequest, exception_list, stop_event):
    """
    create_model_telemetry_metric will receive a json payload to create a metric based on specific telemetry data
    that will be retrieved and a model that must exist at Intelligence layer.

    :param request: The json passed at create_model_metric route.
    :param exception_list: used to catch the error that could occur at the first execution.
    :param stop_event: An Event to signal the alt execution.

    :return: None.
    """
    try:
        start_time = time.time()
        # Run the first cycle
        await repeated_operation(request, exception_list)
        if exception_list:
            raise exception_list[0]
        # Wait for the next time interval, taking into account the time already elapsed
        time_to_next_interval = max(request.step_in_seconds - (time.time() - start_time), 0)
        time.sleep(time_to_next_interval)

        # Start a loop to run the operation repeatedly
        while not stop_event.is_set():
            start_time = time.time()
            # Run the repeated operation
            await repeated_operation(request, exception_list)
            # Wait for the next time interval, taking into account the time already elapsed
            time_to_next_interval = max(request.step_in_seconds - (time.time() - start_time), 0)
            time.sleep(time_to_next_interval)
    except Exception as e:
        return e


# create a metric based telemetry metric provided and model that will run
@app.post('/create_model_metric')
async def create_model_metric_endpoint(request: CreateModelMetricItemRequest):
    """
    create_model_metric route will receive a json payload to create a metric based on specific telemetry data
    that will be retrieved from Grafana and fed to an existing model at Intelligence layer.

    :param request: The json passed will contain:

    - metric_type (mandatory): The metric type.
    - metric_name (mandatory): The name of the metric to be created or retrieved.
    - metric_info (optional): The info of the metric to be created or retrieved.
    - labels (optional): The dictionary of labels that will be set for the metric.
    - states (optional): The list of states if an enum metric is being set for the first time.
    - telemetry_metrics (mandatory). The queries of the telemetry metrics from witch data will be retrieved.
    - model_tag (mandatory): The name of the model where the retrieved telemetry data will be sent.
    - model_type (mandatory): The type of the model where the retrieved telemetry data will be sent.
    - step_in_seconds (optional): The time distance between each sample at telemetry metric. Default is the update rate
    of Prometheus.
    - steps_back (mandatory): The amount of samples that will be used.
    - history_sample_size (optional): TBD
    - data_interruption (optional): TBD
    - history_data (optional): TBD

    According to the metric_type value:

    - Counter = 1
        Counter expects:
        - metric_name (mandatory) -> string. If there is a suffix of _total on the metric name, it will be removed.
        When exposing the time series for counter, a _total suffix will be added. This is for compatibility between
        OpenMetrics and the Prometheus text format, as OpenMetrics requires the _total suffix.
        - metric_info (optional) -> string | None.
        - labels (optional) -> Optional[Dict[str, str | int | float]].
        - states (ignored).
        - telemetry_metrics (mandatory) -> list[str].
        - model_tag (mandatory) -> string.
        - model_type (mandatory) -> string.
        - step_in_seconds (optional) -> int.
        - steps_back (mandatory) -> int.
        - history_sample_size (optional): int | None.
        - data_interruption (optional): bool = False.
        - history_data (optional): list[list[int]].
    - Gauge = 2
        Gauge expects:
        - metric_name (mandatory) -> string.
        - metric_info (optional) -> string | None.
        - labels (optional) -> Optional[Dict[str, str | int | float]].
        - states (ignored).
        - telemetry_metrics (mandatory) -> list[str].
        - model_tag (mandatory) -> string.
        - model_type (mandatory) -> string.
        - step_in_seconds (optional) -> int.
        - steps_back (mandatory) -> int.
        - history_sample_size (optional): int | None.
        - data_interruption (optional): bool = False.
        - history_data (optional): list[list[int]].
    - Info = 3
        Info expects:
        - metric_name (mandatory) -> string.
        - metric_info (optional) -> string | None.
        - labels (optional) -> Optional[Dict[str, str | int | float]].
        - states (ignored).
        - telemetry_metrics (mandatory) -> list[str].
        - model_tag (mandatory) -> string.
        - model_type (mandatory) -> string.
        - step_in_seconds (optional) -> int.
        - steps_back (mandatory) -> int.
        - history_sample_size (optional): int | None.
        - data_interruption (optional): bool = False.
        - history_data (optional): list[list[int]].
    - Enum = 4
        Enum expects:
        - metric_name (mandatory) -> string.
        - metric_info (optional) -> string | None.
        - labels (optional) -> Optional[Dict[str, str | int | float]].
        - states (mandatory at creation of metric): the states that will be the available choice to set the state
         (passed only the first time)
        - telemetry_metrics (mandatory) -> list[str].
        - model_tag (mandatory) -> string.
        - model_type (mandatory) -> string.
        - step_in_seconds (optional) -> int.
        - steps_back (mandatory) -> int.
        - history_sample_size (optional): int | None.
        - data_interruption (optional): bool = False.
        - history_data (optional): list[list[int]].

    :return: a json response 400 if error occurs or 200 if telemetry data are found, model inference is successful and
    model results are sent to Prometheus/Thanos.
    """
    try:
        if request.step_in_seconds and request.step_in_seconds < INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT:
            request.step_in_seconds = INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT
        # Create a stop event for this specific request
        stop_event = threading.Event()
        # Run the first cycle and send immediate response
        exception_list = []

        async def run_first_cycle():
            await create_model_telemetry_metric(request, exception_list, stop_event)

        # Schedule the first cycle as an asyncio task and await its completion
        first_cycle_task = asyncio.create_task(run_first_cycle())
        await first_cycle_task

        if exception_list:
            raise exception_list[0]

        # Store the thread and stop event in the global dictionaries
        threads[request.metric_name] = first_cycle_task
        stop_events[request.metric_name] = stop_event

        return {'message': 'First cycle completed successfully. Metric creation started.'}
    except Exception as e:
        http_err = 'An error occurred in create_model_metric_endpoint: {}'.format(e)
        logger.error(http_err)
        raise HTTPException(status_code=400, detail='{}'.format(e))


@app.post('/stop_model_metrics')
def stop_model_metrics(request: StopModelMetricItemRequest):
    """
    stop_model_metrics route will receive a json payload to stop the metric creations based on specific telemetry data.

    :param request: The json passed will contain:

    - metric_names (mandatory): A list with the names of the metrics to be stopped.

    :return: a json response 200 if the metric creations are stopped successfully even if metric may not exist.
    """
    try:
        for request_metric_name in request.metric_names:
            # Get the metric name
            metric_name = request_metric_name.strip() if request_metric_name else None
            if not metric_name:
                raise HTTPException(status_code=400, detail='metric_name is required.')

            # Stop the corresponding thread
            if metric_name in stop_events:
                stop_events[metric_name].set()
                threads[metric_name].join()
                # Clean up the global dictionaries
                del threads[metric_name]
                del stop_events[metric_name]
            # else:
            #     raise HTTPException(status_code=400, detail='Metric not found.')
        return {'message': 'Metric creation(s) stopped successfully.'}
    except Exception as e:
        http_err = 'An error occurred in stop_model_metric: {}'.format(e)
        logger.error(http_err)
        raise HTTPException(status_code=400, detail='{}'.format(e))


@app.on_event("shutdown")
def shutdown_event():
    for event in stop_events.values():
        event.set()
    for thread in threads.values():
        thread.join()


# TODO: update the TBD.
# create a metric based telemetry metric provided and model that will run
@app.post('/train_model_metric')
async def train_model_metric_endpoint(request: TrainModelMetricItemRequest):
    """
    train_model_metric route will receive a json payload to start a model training at Intelligence layer and then create
    a metric based on that model and the specific telemetry data that will be retrieved.

    :param request: The json passed will contain:

    - labels (optional) -> Dict[str, str | int | float] : The dictionary of labels that will be set for the metric.
    - model_name (mandatory) -> string : The name of the model where the retrieved telemetry data will be sent.
    - model_type (mandatory) -> string : The type of the model to be trained. Possible values: "XGB", "Arima".
    - test_size (mandatory) -> float : A float number between 0 and 1 that will indicate the percentage of test data
    that will be used at training.
    - dataset_name (optional) -> str : The name of the dataframe at Dataclay. If left empty new dataframe will be
    created for the result of Grafana queries.
    - steps_back (mandatory) -> int : The amount of samples that will be used.
    - step_in_seconds (optional): The time distance between each sample at telemetry metric. Default is the update rate
    of Prometheus.
    - max_models_count (optional) -> int : TBD
    - max_mlruns_count (optional) -> int : TBD
    - shap_samples (optional) -> int : TBD
    - model_parameters (mandatory) -> Dictionary: The parameters needed based on the model type that will be trained.
    It must be a dictionary based on the model types:
        - ArimaModelParameters:
            - p (optional) -> int : TBD
            - d (optional) -> int : TBD
            - q (optional) -> int : TBD
        - XGBModelParameters:
            - n_estimators (optional) -> int : TBD
            - max_depth (optional) -> int : TBD
            - eta (optional) -> float : TBD
            - subsample (optional) -> float : TBD
            - colsample_bytree (optional) -> float : TBD
            - alpha (optional) -> int : TBD
    - telemetry_metrics (mandatory) -> list[str] : A list of queries for telemetry metrics from witch data will be
    retrieved.

    :return: a json response 400 if error occurs or 200 if model is created and model inference is successful with
    model results being sent to Prometheus/Thanos.
    """
    try:
        if request.step_in_seconds and request.step_in_seconds < INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT:
            request.step_in_seconds = INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT
        # If dataset names are passed then skip grafana and dataclay steps.
        if request.dataset_name:
            dataset_name = request.dataset_name
        else:
            # step 1 --> using the service account at Grafana create the queries based on the telemetry metrics asked
            grafana_results = await grafana_request(request.telemetry_metrics)
            # FRO MOCK --> create the csv based on the results and save them locally
            # create_and_save_csv_files_from_grafana(grafana_results=grafana_results, model_name=request.model_name)
            # step 2 --> save datasets to dataclay
            await create_and_save_dataframe_to_dataclay(grafana_results=grafana_results, model_name=request.model_name)
            dataset_name = request.model_name

        logger.info('Time: {}, dataset {} created for model training of {}'.format(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], dataset_name, request.model_name))

        # Return a response to the client immediately while continuing the rest of the processing
        asyncio.create_task(continue_training_and_create_metric(request, dataset_name))
        return {'message': 'Dataset created, model training started successfully.'}
    except Exception as e:
        http_err = 'An error occurred in train_model_metric_endpoint: {}'.format(e)
        logger.error(http_err)
        raise HTTPException(status_code=400, detail='{}'.format(e))


async def continue_training_and_create_metric(request, dataset_name):
    try:
        logger.info('Time: {}, calling Intelligence API for model training of {}'.format(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], request.model_name))

        # step 3 --> call CeADAR API and get the response with the model name and type
        model_result_status_code, model_tag, metric_type, metric_states = await call_intelligence_api_train_model(
            request=request, input_data=dataset_name)
        # If model_result_status_code is not 200, exception must be thrown for error with intelligence API
        if model_result_status_code != 200:
            http_err = 'Intelligence API error.'
            logger.error(http_err)
            raise Exception(http_err)

        logger.info('Time: {}, Intelligence API model training of {} completed. Model tag: {}, create metric type: {}, '
                    'with metric states (if exist): {}'.format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                                                               request.model_name, model_tag, metric_type,
                                                               metric_states))

        # step 4 --> call create_model_metric
        logger.info('Time: {}, Model inference of {} started.'.format(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], request.model_name))

        data = request.dict(include={
            'labels',
            'steps_back',
            'telemetry_metrics'
        })
        data['metric_name'] = dataset_name
        data['metric_type'] = metric_type
        if request.step_in_seconds and request.step_in_seconds >= INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT:
            data['step_in_seconds'] = request.step_in_seconds
        else:
            data['step_in_seconds'] = INTERVAL_IN_SECONDS_FOR_METRICS_EXPORT
        data['model_tag'] = model_tag
        data['model_type'] = request.model_type
        data['model_states'] = metric_states

        await create_model_metric_endpoint(CreateModelMetricItemRequest(**data))

    except Exception as e:
        logger.error(f"Error in continue_training_and_create_metric: {e}")
