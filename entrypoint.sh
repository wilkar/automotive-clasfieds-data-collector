#!/bin/bash

python -m src.entrypoints.scrape_data
python -m src.entrypoints.find_intersection
echo "Log file: /var/log/app/project.log"
echo "Offers data: /var/data/app/offers.csv"
echo "Labeling data: /var/data/app/labeling_data.csv"
