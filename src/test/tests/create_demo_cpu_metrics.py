import pandas as pd
import requests
import time
from src.keycloak_request_token import keycloak_request_token


# Load CSV file
df = pd.read_csv("../../cpu_utilization_1min_intervals.csv")

# Request template
url = 'http://10.160.3.20:30734/create_metric'


payload_template = {
    "metric_type": 2,
    "metric_name": "test_demo_cpu_utilization_metric",
    "metric_info": "test demo cpu utilization metric",
    "value": None,  # Will be set dynamically
    "labels": {
        "label1": "test",
        "label2": "demo"
    }
}

# Send each row's value as a new request, looping infinitely
while True:
    for index, row in df.iterrows():
        # Headers, add your authentication here if needed
        headers = {
            'Authorization': 'Bearer {}'.format(keycloak_request_token())
        }
        cpu_value = row["CPU Utilization (%)"]
        payload = payload_template.copy()
        payload["value"] = str(cpu_value)

        try:
            response = requests.post(url, json=payload, headers=headers)
            print(f"Sent: Minute {row['Time (minutes)']} | Value: {cpu_value:.2f} | Status: {response.status_code}")
        except Exception as e:
            print(f"Error sending data: {e}")

        time.sleep(60)  # Wait 60 seconds before sending the next value
