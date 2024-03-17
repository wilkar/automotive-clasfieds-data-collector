import asyncio

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context
from src.models.db_schema import metadata_obj

config = context.config
target_metadata = metadata_obj


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    ini_section = config.get_section(config.config_ini_section)
    if ini_section and "sqlalchemy.url" not in ini_section:
        ini_section[
            "sqlalchemy.url"
        ] = "postgresql+asyncpg://acdc_user:acdc_password@db:5432/acdc_database"

    connectable = AsyncEngine(
        engine_from_config(
            ini_section,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    raise NotImplementedError("offline mode not supported")
else:
    asyncio.run(run_migrations_online())
