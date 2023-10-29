#!/bin/bash

set -e

# Wait for the database to be ready, if necessary (using wait-for-it.sh or similar)

alembic upgrade head

exec gunicorn src.entrypoints.api.app:app


# python -m src.entrypoints.scrape_data
# python -m src.entrypoints.find_intersection
# echo "Log file: /var/log/app/project.log"
# echo "Offers data: /var/data/app/offers.csv"
# echo "Labeling data: /var/data/app/labeling_data.csv"
