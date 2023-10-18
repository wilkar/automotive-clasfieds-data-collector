import json
import logging.config

json_file = "src/config/logging_config.json"


def setup_logging():
    with open(json_file, "r") as f:
        config = json.load(f)
    logging.config.dictConfig(config)
