import csv

def get_balanced_dataset(input_file: str, output_file: str):
    with open(input_file, 'r') as input_file:
        csv_reader = csv.DictReader(input_file)

        suspicious_offers: list = []
        non_suspicious_offers: list = []

        for offer in csv_reader:
            vin = offer["VIN"]
            lowercase_vin = vin.lower()

            if lowercase_vin == 'xxxxxxxxxxxxxxxxx' or len(set(vin)) <= 3:
                offer["Suspicious"] = "1"
                suspicious_offers.append(offer)
            elif vin:
                offer["Suspicious"] = "0"
                non_suspicious_offers.append(offer)

        non_suspicious_offers = non_suspicious_offers[:len(suspicious_offers)]
        combined_list = suspicious_offers + non_suspicious_offers

    with open(output_file, 'w') as output_file:
        fieldnames = list(combined_list[0].keys())
        csv_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        csv_writer.writeheader()

        for offer in combined_list:
            csv_writer.writerow(offer)

get_balanced_dataset("training_data.csv", "balanced_set.csv")