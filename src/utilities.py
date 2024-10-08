import re


def format_metric_string(metric_string):
    # Step 1: Extract the metric name (before the '{')
    metric_name = metric_string.split('{')[0]

    # Step 2: Extract the key-value pairs inside the curly braces
    inside_braces = re.search(r'{(.*?)}', metric_string)
    if not inside_braces:
        return metric_name

    # Step 3: Split the key-value pairs and format them
    key_value_pairs = inside_braces.group(1).split(', ')
    formatted_pairs = []

    for pair in key_value_pairs:
        key, value = pair.split('=')
        # Clean up the quotes from the value
        value = value.strip('"')
        formatted_pairs.append(f"{key}_{value}")

    # Step 4: Combine the metric name with the formatted key-value pairs
    formatted_string = f"{metric_name}_{'_'.join(formatted_pairs)}"

    return formatted_string

# # Example usage
# input_string = 'scaph_host_power_microwatts{job="scaphandre", instance="192.168.2.60:30080"} / 1000000'
# formatted_result = format_metric_string(input_string)
#
# print(formatted_result)