import csv


def find_common_vins(labeling_data_file, offers_file) -> tuple[int, set[str], int, int]:
    with open(labeling_data_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)
        labeling_vins = {row[0] for row in reader}

    with open(offers_file, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)
        offers_vins: list = []
        for row in reader:
            if row[6] != "[None]":
                clean_vin = (
                    row[6]
                    .replace("[", "")
                    .replace("]", "")
                    .replace(" ", "")
                    .replace("'", "")
                )
                offers_vins.append(clean_vin)

    common_vins = labeling_vins.intersection(offers_vins)
    common_vins_count = len(common_vins)
    total_offers_count = len(offers_vins)
    labeling_vin_count = len(labeling_vins)
    return common_vins_count, common_vins, total_offers_count, labeling_vin_count


labeling_data_file = "labeling_data.csv"
offers_file = "offers.csv"

(
    common_vins_count,
    common_vins,
    total_offers_count,
    labeling_vin_count,
) = find_common_vins(labeling_data_file, offers_file)
print(f"Number of scraped offers {total_offers_count}")
print(f"Number of fetched labeling VIN ids {labeling_vin_count}")
print(f"Number of common VINs: {common_vins_count}")
print(f"Common VINs: {common_vins}")
