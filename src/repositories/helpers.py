from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config.config_main import DB_URL


def get_engine() -> AsyncEngine:
    return create_async_engine(DB_URL, echo=True)
