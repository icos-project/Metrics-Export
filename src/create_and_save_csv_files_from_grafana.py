import pandas as pd


def create_and_save_csv_files_from_grafana(grafana_results, model_name: str):
    combined_data = {}

    # Iterate over the results to build the combined dataset
    for item in grafana_results:
        for key, values in item.items():
            # For each key, iterate over its values and merge into combined_data
            for entry in values:
                time_value = entry['time']
                value = entry['value']

                # Initialize time key if not exists
                if time_value not in combined_data:
                    combined_data[time_value] = {'time': time_value}

                # Add the value under the corresponding key (column name)
                combined_data[time_value][key] = value

    # Convert combined_data to a list of dictionaries and then a pandas DataFrame
    combined_data_list = list(combined_data.values())
    df = pd.DataFrame(combined_data_list)

    # Save the DataFrame to a CSV file
    df.to_csv('{}.csv'.format(model_name), index=False)

    print('Dataset created and saved to combined_dataset.csv')
