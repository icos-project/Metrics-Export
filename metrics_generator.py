import os
import time
from flask import Flask, request, jsonify
from prometheus_client import Gauge, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Initialize Flask
app = Flask(__name__)

# Initialize a Gauge metric
g = Gauge('intelligence_layer_model', 'Intelligence layer info', ['model'])


@app.route('/process_model', methods=['POST'])
def process_model():
    # Parse model and result from the request
    data = request.json
    model = data.get('model')
    result = data.get('result')
    if not model or result is None:
        return jsonify({'error': 'Model and result are required.'}), 400

    g.labels(model=model).set_to_current_time()   # Set to current unixtime
    # Set the gauge with the model label and result value
    g.labels(model=model).set(result)
    return jsonify({'message': 'Metric updated successfully.'}), 200


# Combine Flask app and Prometheus metrics app
app_dispatch = DispatcherMiddleware(app, {
    '/metrics': make_wsgi_app()
})

if __name__ == '__main__':
    # Start up the server to expose the metrics and Flask app
    port = int(os.getenv('PORT', '8000'))
    run_simple(hostname="0.0.0.0", port=port, application=app_dispatch)


# FOR TESTING PURPOSE
# metrics_generator.py
# import time
# from prometheus_client import start_http_server, Gauge
#
# g = Gauge('intelligence_layer_model', 'intelligence layer info', ['model'])
#
#
# def process_model(model, result):
#     g.labels(model=model).set(result)
#
#
# if __name__ == '__main__':
#     # Start up the server to expose the metrics.
#     start_http_server(8000)
#     # Generate some requests.
#     counter = 1
#     while True:
#         counter = counter + 1
#         # process_model('model_name_{}'.format(counter), str(counter))
#         process_model('model_name_1'.format(counter), str(counter))
#         time.sleep(1)
