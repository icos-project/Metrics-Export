import requests

from src.environment_variables import AGGREGATOR_URL
from src.keycloak_request_token import keycloak_request_token

url_aggregator = AGGREGATOR_URL
# Headers, add your authentication here if needed
headers = {
    'Authorization': 'Bearer {}'.format(keycloak_request_token())
}
old_nodes = []


def aggregator_request():
    global old_nodes

    response = requests.get(url_aggregator, headers=headers)
    if response.status_code == 200:
        # get the result
        res = response.json()
        # extract icos agent id and kubernetes node names
        result = process_nodes(res)
        new_nodes, common_and_new_nodes, removed_nodes = compare_node_arrays(old_nodes, result)
        old_nodes = common_and_new_nodes
        return new_nodes, removed_nodes
    else:
        return [], []


def process_nodes(json_data):
    nodes_dict = []

    for cluster in json_data.get('cluster', []):
        for node in json_data['cluster'][cluster].get('node', []):
            icos_agent_id = json_data['cluster'][cluster].get('icosAgentID', '')
            node_name = node
            icos_host_id = json_data['cluster'][cluster]['node'][node]['uuid']

            nodes_dict.append({'icos_agent_id': icos_agent_id, 'node_name':  node_name, 'icos_host_id': icos_host_id})

    return nodes_dict


def compare_node_arrays(old_array, new_array):
    old_set = {tuple(d.items()) for d in old_array}  # Convert dicts to tuples for easy comparison
    new_set = {tuple(d.items()) for d in new_array}

    new_nodes = [dict(item) for item in new_set - old_set]  # Includes all new items
    common_and_new_nodes = [dict(item) for item in new_set]  # Includes all new items and common ones
    removed_nodes = [dict(item) for item in old_set - new_set]  # Items in old but not in new

    return new_nodes, common_and_new_nodes, removed_nodes

