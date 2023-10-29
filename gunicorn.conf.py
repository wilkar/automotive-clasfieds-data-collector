import json
import logging

from src.config import log_init

log_init.setup_logging()

logger = logging.getLogger(__name__)

access_logfile = "-"
error_logfile = "-"
workers = 3
pid = "/app/gunicorn.pid"
bind = "0.0.0.0:8008"
timeout = 120
limit_request_line = 8192
worker_class = "uvicorn.workers.UvicornWorker"
reload = False

with open("src/config/logging_config.json", "r") as f:
    logconfig_dict = json.load(f)
