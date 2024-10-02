from dataclay import Client
from src.dataclay_model_dataframes import PersistentDF
import pandas as pd
from pandas import DataFrame
from src.environment_variables import DATACLAY_HOST, DATACLAY_USERNAME, DATACLAY_PASSWORD


def dataclay_dataframe_store(dataset_name: str, dataset_dataframe: DataFrame):
    client = Client(host=DATACLAY_HOST, username=DATACLAY_USERNAME, password=DATACLAY_PASSWORD, dataset=dataset_name)
    client.start()

    pdf = PersistentDF(dataset_dataframe)
    pdf.make_persistent(alias="{}_dataset".format(dataset_name))


def create_and_save_dataframe_to_dataclay(grafana_results):
    dataset_names = []
    for item in grafana_results:
        # Each item is a dictionary, get the key and the associated list of values
        for key, values in item.items():
            # Create a pandas DataFrame from the list of dictionaries (values)
            df = pd.DataFrame(values)

            # Ensure that the DataFrame has 'time' and 'value' as columns
            df = df[['time', 'value']]

            dataclay_dataframe_store(dataset_name=key, dataset_dataframe=df)
            dataset_names.append(key)
    return dataset_names



