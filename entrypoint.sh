#!/bin/bash

python -m src.entrypoints.scrape_data
python -m src.entrypoints.find_intersection
echo "Log file: /var/log/app/output/project.log"
echo "Offers data: /var/data/app/output/offers.csv"
echo "Labeling data: /var/data/app/output/labeling_data.csv"
