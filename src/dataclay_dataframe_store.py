from dataclay import Client
from src.dataclay_model_dataframes import PersistentDF
import pandas as pd
from pandas import DataFrame
from src.environment_variables import DATACLAY_HOST, DATACLAY_USERNAME, DATACLAY_PASSWORD


async def dataclay_dataframe_store(dataset_name: str, dataset_dataframe: DataFrame):
    client = Client(host=DATACLAY_HOST, username=DATACLAY_USERNAME, password=DATACLAY_PASSWORD, dataset=dataset_name)
    client.start()

    pdf = PersistentDF(dataset_dataframe)
    pdf.make_persistent(alias="{}_dataset".format(dataset_name))


def create_dataframe(grafana_results):
    combined_data = {}

    for item in grafana_results:
        # Each item is a dictionary, get the key and the associated list of values
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

    return df


async def create_and_save_dataframe_to_dataclay(grafana_results, model_name: str):
    df = create_dataframe(grafana_results)

    await dataclay_dataframe_store(dataset_name=model_name, dataset_dataframe=df)
    return



