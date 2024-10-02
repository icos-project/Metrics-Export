import csv


def create_and_save_csv_files_from_grafana(grafana_results):
    # print('data: ', grafana_results)
    print('len: ', len(grafana_results))
    for item in grafana_results:
        # Each item is a dictionary, get the key and the associated list of values
        for key, values in item.items():
            # Create the filename using the key
            filename = f'{key}.csv'

            print('filename: ', filename)

            # Open the file in write mode
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)

                # Write the header
                writer.writerow(['time', 'value'])

                # Write the rows (time and value pairs)
                for entry in values:
                    writer.writerow([entry['time'], entry['value']])

