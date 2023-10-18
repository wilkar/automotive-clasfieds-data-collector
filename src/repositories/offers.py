# from dataclasses import dataclass

# from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

# from src.raw_offer import RawOffer
# from src.repositories.db_schema import offers
from src.entrypoints.create_db import get_engine


class OffersRepo:
    def __init__(self, engine: AsyncEngine | None = None) -> None:
        self.engine = engine or get_engine()

    async def add_offers(self):
        pass
