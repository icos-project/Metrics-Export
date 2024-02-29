import os
from flask import Flask, request, jsonify
from prometheus_client import Gauge, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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

    logger.info('Time: {}, model: {}, result: {}'.format(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], model,
                                                         result))

    if not model or result is None:
        return jsonify({'error': 'Model and result are required.'}), 400

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
