# Automotive classfields data collector

## About

Web scraping and data analysis tool for detecting fraulent automotive classfieds.

## Current state

Implemented basic funcionality: fetching training data, fetching classfieds from olx, getting intersection

## End goal

General goal is to create an app that can continuosly collect data and flag fraulent classfieds.

## Usage
### Local
1. `poetry install` to install dependencies
2. `poetry shell` to activate venv
3. `python -m src.entrypoints.scrape_data.py` to run scraping proces. Note: logs will be saved in project main dir in file `project.log`
4. `python -m src.entrypoints.find_intersection.py` to get number of common datapoints
### Docker
1. `docker-compose up --build`builds the container and runs the process. Log files are accessible from the container 
   
## TODO

- Complete database setup
- Add more data sources
- Implement async in the whole project
- Add tests
- Add ML model
- Add frontend for data visualisation