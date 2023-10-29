import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from src.models.db_schema import (
    labeling_data,
    offer_location,
    offers_base,
    offers_details,
)
from src.repositories.helpers import get_engine
from src.repositories.offer.base import OfferRepository


class SqlAlchemyOfferRepository(OfferRepository):
    def __init__(self, engine: AsyncEngine | None = None) -> None:
        self.engine = engine or get_engine()

    async def add_base_offer_info(
        self,
        brand: str,
        clasfieds_id: int,
        link: str,
        title: str,
        created_time: str,
        description: str,
        image_link: str,
        vin: str,
        scraped_time: datetime.datetime,
    ) -> None:
        ins = (
            insert(offers_base)
            .values(
                brand=brand,
                clasfieds_id=clasfieds_id,
                link=link,
                title=title,
                created_time=created_time,
                description=description,
                image_link=image_link,
                vin=vin,
                scraped_time=scraped_time,
            )
            .on_conflict_do_nothing()
        )
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def add_location_offer_info(
        self, clasfieds_id: str, region: str, city: str
    ) -> None:
        ins = (
            insert(offer_location)
            .values(clasfieds_id=clasfieds_id, region=region, city=city)
            .on_conflict_do_nothing()
        )
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def add_params_offer_info(
        self,
        clasfieds_id: str,
        model: str,
        price: int,
        engine_size: int,
        manufactured_year: int,
        petrol: str,
        car_body: str,
        milage: int,
        color: str,
        condition: str,
        transmission: str,
        country_origin: str,
        righthanddrive: str,
    ) -> None:
        ins = (
            insert(offers_details)
            .values(
                clasfieds_id=clasfieds_id,
                model=model,
                price=price,
                engine_size=engine_size,
                manufactured_year=manufactured_year,
                petrol=petrol,
                car_body=car_body,
                milage=milage,
                color=color,
                condition=condition,
                transmission=transmission,
                country_origin=country_origin,
                righthanddrive=righthanddrive,
            )
            .on_conflict_do_nothing()
        )
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def add_labeling_data(self, vin: str) -> None:
        ins = insert(labeling_data).values(vin=vin).on_conflict_do_nothing()
        async with self.engine.begin() as conn:
            await conn.execute(ins)
