metric_definitions = [
    {
        'metric_name': 'intelligence_node_cpu_utilization_prediction',
        'model_tag': 'metrics_utilization_model_xgb:latest',
        'step_in_seconds': 60,
        'steps_back': 12,
        'labels': {
            'model_name': 'metrics_utilization_model_xgb:latest',
            'model_type': 'XGB',
            'step_in_seconds': '60',
            'sequence_size': '12'
        },
        'telemetry_template': '(1 - avg(irate(node_cpu_seconds_total{{mode="idle", icos_agent_id="{icos_agent_id}", icos_host_id="{icos_host_id}"}}[2m])) without (cpu,mode)) * 100'
    },
    {
        'metric_name': 'intelligence_node_memory_utilization_prediction',
        'model_tag': 'metrics_utilization_model_xgb:latest',
        'step_in_seconds': 60,
        'steps_back': 12,
        'labels': {
            'model_name': 'metrics_utilization_model_xgb:latest',
            'model_type': 'XGB',
            'step_in_seconds': '60',
            'sequence_size': '12'
        },
        'telemetry_template': '100 * (1 - ((avg_over_time(node_memory_MemFree_bytes{{icos_agent_id="{icos_agent_id}", icos_host_id="{icos_host_id}"}}[10m]) + '
                              'avg_over_time(node_memory_Cached_bytes{{icos_agent_id="{icos_agent_id}", icos_host_id="{icos_host_id}"}}[10m]) + '
                              'avg_over_time(node_memory_Buffers_bytes{{icos_agent_id="{icos_agent_id}", icos_host_id="{icos_host_id}"}}[10m])) / '
                              'avg_over_time(node_memory_MemTotal_bytes{{icos_agent_id="{icos_agent_id}", icos_host_id="{icos_host_id}"}}[10m])))'
    },
    {
        'metric_name': 'intelligence_node_energy_consumption_prediction',
        'model_tag': 'lstm_model:latest',
        'step_in_seconds': 60,
        'steps_back': 100,
        'labels': {
            'model_name': 'lstm_model:latest',
            'model_type': 'XGB',
            'step_in_seconds': '60',
            'sequence_size': '100'
        },
        'telemetry_template': 'scaph_host_power_microwatts{{icos_agent_id=\"{icos_agent_id}\", k8s_node_name=\"{node_name}\"}}'
    }
]

nodes = [
    { 'icos_agent_id': 1, 'node_name': 'a', 'icos_host_id': '1'},
    { 'icos_agent_id': 2, 'node_name': 'b', 'icos_host_id': '2'},
    { 'icos_agent_id': 3, 'node_name': 'c', 'icos_host_id': '3'},
]
for node in nodes:

    icos_agent_id = node['icos_agent_id']
    node_name = node['node_name']
    icos_host_id = node['icos_host_id']

    for metric in metric_definitions:
        labels = {'icos_agent_id': icos_agent_id, 'node_name': node_name, 'icos_host_id': icos_host_id}
        labels.update(metric['labels'])  # Merge any additional labels

        telemetry_metrics = [metric['telemetry_template'].format(
            icos_agent_id=icos_agent_id, icos_host_id=icos_host_id, node_name=node_name
        )]

        print(telemetry_metrics)