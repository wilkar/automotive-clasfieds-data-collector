import os
from pathlib import Path

from src.env import env_bool

SRC_DIR = Path(__file__).resolve().parent.parent

DEVELOPMENT = env_bool("DEVELOPMENT", default_value=False)
DEBUG_LOG = env_bool("DEBUG_LOG", default_value=DEVELOPMENT)
DB_URL = os.environ.get(
    "DB_URL", "postgresql+asyncpg://acdc_user:acdc_password@db:5432/acdc_database"
)
