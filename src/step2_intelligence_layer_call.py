import requests
import json
from fastapi import HTTPException
from src.environment_variables import INTELLIGENCE_API_MODEL_INFERENCE_BASE_URL, INTELLIGENCE_API_MODEL_TRAINING_URL
from src.metric_helpers import CreateModelMetricItemRequest, TrainModelMetricItemRequest


def prepare_results_for_model_input(results, steps_back):
    """
    Takes the results from the prometheus/Thanos query and prepares them as an input for the model call.

    :param results: The results returned from grafana query.
    :param steps_back: The amount of past values that the model will take as input.

    :return: An array with the results
    """
    refactored_data = {}
    for item in results:
        for key, value_list in item.items():
            # Extract only the 'value' fields
            values = [entry['value'] for entry in value_list]
            # Fill with 0s if the list is shorter than the target_length
            if len(values) < steps_back:
                values.extend([0] * (steps_back - len(values)))
            # Truncate the list if it's longer than the target_length
            values = values[:steps_back]
            # Add to the refactored dictionary
            refactored_data[key] = values

    return refactored_data


def call_intelligence_api_infer_model(request: CreateModelMetricItemRequest, input_data):
    """
    This function will call the intelligence api endpoint that corresponds to the model name passed for model inference
    with the data provided.

    :param request: The request from which information to call Intelligence API for the model inference will be
    retrieved.
    :param input_data: The data to pass to the model.

    :return: Response status code and response data as a json.
    """
    url = INTELLIGENCE_API_MODEL_INFERENCE_BASE_URL
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        "model_tag": request.model_tag,
        "model_type": request.model_type.value,
        "steps_back": request.steps_back,
        "history_sample_size": request.history_sample_size,
        "data_interruption": request.data_interruption,
        "history_data": request.history_data,
        "input_series": input_data
    })
    print("data: ", data)
    try:
        response = requests.post(url, headers=headers, data=data)
        return response.status_code, response.json()
    except Exception as e:
        # If model_result_status_code is not 200, exception must be thrown for error with intelligence API
        # communication
        message = 'Intelligence API error or endpoint does not exist. Error: {}'.format(e)
        # Raise the HTTPException for FastAPI to handle
        raise HTTPException(status_code=400, detail='{}'.format(message))


def call_intelligence_api_train_model(request: TrainModelMetricItemRequest, input_data):
    """
    This function will call the intelligence api endpoint that corresponds to a model training with the dataset name
    passed at input data.

    :param request: The request from which information to call Intelligence API for the model training will be
    retrieved.
    :param input_data: The dataset names to use for the model training.

    :return: Response status code and response data as a json.
    """
    url = INTELLIGENCE_API_MODEL_TRAINING_URL
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        "model_name": request.model_name,
        "model_type": request.model_type.value,
        "test_size": request.test_size,
        "dataset_name": input_data,
        "steps_back": request.steps_back,
        "max_models_count": request.max_models_count,
        "max_mlruns_count": request.max_mlruns_count,
        "shap_samples": request.shap_samples,
        "model_parameters": request.model_parameters.dict(),
    })
    try:
        response = requests.post(url, headers=headers, data=data)
        return response.status_code, response.json()
    except Exception as e:
        # If model_result_status_code is not 200, exception must be thrown for error with intelligence API
        # communication
        message = 'Intelligence API error. Error: {}'.format(e)
        # Raise the HTTPException for FastAPI to handle
        raise HTTPException(status_code=400, detail='{}'.format(message))

