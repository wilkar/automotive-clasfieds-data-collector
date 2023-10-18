import os
from distutils.util import strtobool

DEVELOPMENT = bool(strtobool(os.getenv("DEVELOPMENT", "false")))
DEBUG_LOG = bool(strtobool(os.getenv("DEBUG_LOG", str(DEVELOPMENT))))
DB_URL = os.environ.get(
    "DB_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/data_app_db"
)
