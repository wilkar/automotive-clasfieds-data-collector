import logging
from logging.config import dictConfig as dict_config
from typing import TYPE_CHECKING

from src.config.main_config import DEBUG_LOG

if TYPE_CHECKING:
    from logging.config import _LoggerConfiguration


def init_logging() -> None:
    default_handlers = ["json-stdout", "json-stderr"]
    info_logger_config: _LoggerConfiguration = {
        "level": "INFO",
        "handlers": default_handlers,
    }

    logging_config: dict = {
        "version": 1,
        "disable_existing_loggers": True,
        "root": {
            "handlers": ["null"],
        },
        "loggers": {
            "src": info_logger_config,
            "__main__": info_logger_config,
            "src.raw_offer_producers.rate_limiter": {
                "level": "INFO",
                "handler": default_handlers,
            },
        },
        "filters": {
            "max-level": {
                "highest_log_level": logging.WARNING,
            },
        },
        "handlers": {
            "json-stdout": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
                "filters": ["max-level"],
            },
            "json-stderr": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stderr",
                "level": "WARNING",
            },
            "null": {
                "class": "logging.NullHandler",
            },
        },
        "formatters": {
            "json": {
                "format": "%(asctime)s %(levelname)s %(message)s %(name)s",
            },
            "debug": {
                "format": "%(asctime)s |%(levelname)s| %(message)s [%(name)s]",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
    }
    if DEBUG_LOG:
        for handler in logging_config["handlers"].values():
            handler["formatter"] = "debug"

    dict_config(logging_config)
