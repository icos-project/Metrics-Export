import os
from flask import Flask, request, jsonify
from prometheus_client import make_wsgi_app, REGISTRY
from prometheus_client.core import CollectorRegistry
from prometheus_client.multiprocess import MultiProcessCollector
from metric_types_functions import counter, gauge, info
from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware# for swagger
from flask_restx import Api, Resource, reqparse
import logging
from datetime import datetime
from enum import Enum

# get the registry of the metrics
registry = CollectorRegistry()
MultiProcessCollector(registry)

# set a typical logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask
app = Flask(__name__)

# Initialize Api
api = Api(app, version='1.0', title='Metrics Generator API', description='A simple API for generating metrics')


# create the enums of metric types
class MetricType(Enum):
    Counter = 1
    Gauge = 2
    Summary = 3
    Histogram = 4
    Info = 5
    Enum = 6
    Exemplars = 7


# Function to get an existing metric by name from the registry
def get_metric_by_name(metric_name):
    for collector in REGISTRY._collector_to_names.keys():
        # Check if this collector is the one we're looking for based on its name
        if metric_name in REGISTRY._collector_to_names[collector]:
            return collector
    return None


# @app.route('/process_model', methods=['POST'])
# Define your Flask-RESTX Resource (previously your Flask route)
@api.route('/process_model')  # Use the api.route decorator
class ProcessModel(Resource):
    @api.doc('process_model')
    def process_model(self):
        """
        process_model route will receive a json payload with a model and a result property.
        Model property is the name of the model.
        Result property is the value of the model prediction.
        After getting the properties it creates a gauge metric that has as a property the model name and as a value the
        result value.

        :return: a json response with 400 if error occurs or 200 if metric is saved successfully.
        """
        # Parse request
        data = request.json
        # get the metrics type value. Default is Gauge
        metric_type_value = data.get('type_of_metric', 2)
        # get the metric name
        metric_name = data.get('metric_name', None)
        # get the value passed
        value = data.get('value', None)
        # get metric info
        metric_info = data.get('metric_info', None)
        # get metric labels
        labels = data.get('labels', {})

        # Convert the incoming metric type value to MetricType enum
        try:
            metric_type = MetricType(metric_type_value)
        except ValueError:
            return {'error': 'Invalid metric type'}, 400

        # if metric name or value are not passed then return error
        if metric_name is None or value is None:
            logger.error('metric_name and value not passed.')
            return jsonify({'error': 'metric_name and value are required.'}), 400

        # check if metric already exists
        # if it already exists then just update it at the metric runs
        existing_metric = get_metric_by_name(metric_name)

        logger.info('Time: {}, metrics name: {}, value: {}'.format(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], metric_name, value))

        # Update the appropriate metric based on the enum
        if metric_type == MetricType.Counter:
            counter(existing_metric, metric_name, metric_info, labels, value)
        elif metric_type == MetricType.Gauge:
            gauge(existing_metric, metric_name, metric_info, labels, value)
        # elif metric_type == MetricType.Summary:
        # elif metric_type == MetricType.Histogram:
        elif metric_type == MetricType.Info:
            info(existing_metric, metric_name, metric_info, value)
        # elif metric_type == MetricType.Enum:
        # elif metric_type == MetricType.Exemplars:

        return jsonify({'message': 'Metric updated successfully.'}), 200


# Combine Flask app and Prometheus metrics app
app_dispatch = DispatcherMiddleware(app, {
    '/metrics': make_wsgi_app(registry)
})

if __name__ == '__main__':
    # Start up the server to expose the metrics and Flask app
    port = int(os.getenv('PORT', '8000'))
    run_simple(hostname="0.0.0.0", port=port, application=app_dispatch)
