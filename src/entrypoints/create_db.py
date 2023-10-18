# work in progress...
import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.config.config_main import DB_URL
from src.models.db_schema import metadata_obj


def get_engine() -> AsyncEngine:
    print(DB_URL)
    return create_async_engine(DB_URL, echo=True)


async def setup() -> None:
    async with get_engine().begin() as conn:
        await conn.run_sync(metadata_obj.create_all)


if __name__ == "__main__":
    asyncio.run(setup())
