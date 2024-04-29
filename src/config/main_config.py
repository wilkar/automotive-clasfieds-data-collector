import os
from pathlib import Path

from sklearn.ensemble import (
    AdaBoostClassifier,  # type: ignore
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression  # type: ignore
from sklearn.neighbors import KNeighborsClassifier  # type: ignore

from src.env import env_bool

SRC_DIR = Path(__file__).resolve().parent.parent

DEVELOPMENT = env_bool("DEVELOPMENT", default_value=False)
DEBUG_LOG = env_bool("DEBUG_LOG", default_value=DEVELOPMENT)
DB_URL = os.environ.get(
    "DB_URL",
    "postgresql+asyncpg://acdc_user:acdc_password@localhost:5432/acdc_database",
)


models = {
    "LogisticRegression": LogisticRegression(),
    "RandomForestClassifier": RandomForestClassifier(),
    "GradientBoostingClassifier": GradientBoostingClassifier(),
    "AdaBoostClassifier": AdaBoostClassifier(),
    "ExtraTreesClassifier": ExtraTreesClassifier(),
    "KNeighborsClassifier": KNeighborsClassifier(),
}
