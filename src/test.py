# test_logging.py
import logging

from src.config.log_init import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Explicitly set logging level
logger.info("This is a test log message")
