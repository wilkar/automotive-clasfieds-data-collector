import logging

from src.bootstrap.app import build_app_container
from src.config import log_init
from src.entrypoints.api.main import get_app

log_init.setup_logging()

logger = logging.getLogger(__name__)
app = get_app(build_app_container())
