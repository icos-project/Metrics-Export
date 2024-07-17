import requests
import json
from fastapi import HTTPException
from src.environment_variables import INTELLIGENCE_API_BASE_URL
from src.metric_helpers import CreateModelMetricItemRequest


def prepare_results_for_model_input(results, sequence_size):
    """
    Takes the results from the prometheus/Thanos query and prepares them as an input for the model call.

    :param results: The results returned from prometheus/Thanos query, a list of tuples.
    :param sequence_size: The amount of past values that the model will take as input.

    :return: An array with the results
    """
    # Extract the second value from each tuple that is the metric value
    extracted_values = [value[1] for value in results]
    # Desired size of the new list is the sequence size provided
    desired_size = sequence_size
    # Prepend zeros if the extracted list is smaller than the desired size
    if len(extracted_values) < desired_size:
        extracted_values = [0] * (desired_size - len(extracted_values)) + extracted_values
    if len(extracted_values) > desired_size:
        extracted_values = extracted_values[len(extracted_values) - desired_size:]
    return extracted_values


def call_intelligence_api_model(request: CreateModelMetricItemRequest, input_data):
    """
    This function will call the intelligence api endpoint that corresponds to the model name passed with the data
    provided.

    :param request: The request from which information to call Intelligence API for the model inference will be
    retrieved.
    :param input_data: The data to pass to the model.

    :return: Response status code and response data as a json.
    """
    url = INTELLIGENCE_API_BASE_URL + request.model_route
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        "model_tag": request.model_name,
        "model_type": request.model_type,
        "input_series": input_data
    })
    try:
        response = requests.post(url, headers=headers, data=data)
        return response.status_code, response.json()
    except Exception as e:
        # If model_result_status_code is not 200, exception must be thrown for error with intelligence API
        # communication
        message = 'Intelligence API error or endpoint does not exist. Error: {}'.format(e)
        # Raise the HTTPException for FastAPI to handle
        raise HTTPException(status_code=400, detail='{}'.format(message))
