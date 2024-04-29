from datetime import datetime, timezone

from sqlalchemy import and_, func, join, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine

from src.models.db_schema import (
    labeling_data,
    offer_location,
    offers_base,
    offers_details,
    suspicious_offers,
    suspicious_offers_v2,
)
from src.models.raw_offer import (
    RawOffer,
    RawOfferLocation,
    RawOfferParameters,
    SuspiciousOffer,
)
from src.repositories.helpers import get_engine
from src.repositories.offer.base import OfferRepository


class SqlAlchemyOfferRepository(OfferRepository):
    def __init__(self, engine: AsyncEngine | None = None) -> None:
        self.engine = engine or get_engine()

    async def add_base_offer_info(self, raw_offer: RawOffer) -> None:
        if isinstance(raw_offer.created_time, str):
            dt_with_tz = datetime.fromisoformat(raw_offer.created_time)
            created_time = dt_with_tz.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            created_time = None

        if isinstance(raw_offer.scraped_time, str):
            dt_with_tz = datetime.fromisoformat(raw_offer.scraped_time)
            scraped_time = dt_with_tz.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            scraped_time = None
        ins = (
            insert(offers_base)
            .values(
                brand=raw_offer.brand,
                clasfieds_id=raw_offer.id,
                link=raw_offer.link,
                title=raw_offer.title,
                created_time=created_time,
                description=raw_offer.description,
                image_links=raw_offer.image_links,
                vin=raw_offer.vin,
                scraperd_time=scraped_time,
            )
            .on_conflict_do_nothing()
        )
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def add_location_offer_info(
        self, raw_offer_location: RawOfferLocation
    ) -> None:
        ins = (
            insert(offer_location)
            .values(
                clasfieds_id=raw_offer_location.id,
                region=raw_offer_location.region,
                city=raw_offer_location.city,
            )
            .on_conflict_do_nothing()
        )
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def add_params_offer_info(self, offer_parameters: RawOfferParameters) -> None:
        ins = (
            insert(offers_details)
            .values(
                clasfieds_id=offer_parameters.id,
                model=offer_parameters.model,
                price=offer_parameters.price,
                engine_size=offer_parameters.engine_size,
                manufactured_year=offer_parameters.manufactured_year,
                petrol=offer_parameters.petrol,
                car_body=offer_parameters.car_body,
                milage=offer_parameters.milage,
                color=offer_parameters.color,
                condition=offer_parameters.condition,
                transmission=offer_parameters.transmission,
                country_origin=offer_parameters.country_origin,
                righthanddrive=offer_parameters.righthanddrive,
            )
            .on_conflict_do_nothing()
        )
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def add_labeling_data(self, vin: str) -> None:
        ins = insert(labeling_data).values(vin=vin).on_conflict_do_nothing()
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def select_labeling_data(self, vin: str) -> bool:
        query = select(labeling_data).where(labeling_data.c.vin == vin)
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            data = result.fetchone()
            return data is not None

    async def select_single_base_offer(self, clasfieds_id: int):
        query = select(offers_base).where(offers_base.c.clasfieds_id == clasfieds_id)
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            data = result.fetchone()
            return data

    async def select_all_offers(self):
        query = (
            select(
                offers_base.c.clasfieds_id,
                offers_base.c.title,
                offers_base.c.description,
                offers_base.c.vin,
                offers_details.c.model,
                offers_details.c.price,
                offers_details.c.milage,
                offers_details.c.condition,
                offers_details.c.country_origin,
            )
            .select_from(
                join(
                    offers_base,
                    offers_details,
                    offers_base.c.clasfieds_id == offers_details.c.clasfieds_id,
                )
            )
            .where(
                and_(
                    offers_details.c.model.isnot(None),
                    offers_details.c.price.isnot(None),
                    offers_details.c.milage.isnot(None),
                    offers_details.c.condition.isnot(None),
                    offers_details.c.country_origin.isnot(None),
                    func.lower(offers_base.c.brand).in_(
                        [
                            "opel",
                            "ford",
                            "renault",
                            "audi",
                            "peugeot",
                            "skoda",
                            "toyota",
                            "volkswagen",
                            "bmw",
                            "volvo",
                            "hyundai",
                            "kia",
                            "mercedes-benz",
                            "nissan",
                            "citroën",
                            "fiat",
                            "seat",
                            "mazda",
                            "honda",
                            "suzuki",
                            "jeep",
                            "mitsubishi",
                            "dacia",
                            "porsche",
                            "chevrolet",
                            "lexus",
                            "alfa romeo",
                            "mini",
                            "land rover",
                            "dodge",
                            "jaguar",
                            "subaru",
                            "chrysler",
                            "mercedes",
                            "saab",
                            "citroen",
                            "smart",
                            "infiniti",
                            "ssangYong",
                            "lancia",
                            "daihatsu",
                            "daewoo",
                            "aixam",
                            "cadillac",
                            "polonez",
                        ]
                    ),
                )
            )
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            data = result.fetchall()
            return data

    async def select_all_suspicious_offers(self):
        query = select(suspicious_offers)
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            data = result.fetchall()
            return data

    async def select_single_suspicious_offer(self, clasfieds_offer_id: int):
        query = select(suspicious_offers).where(
            suspicious_offers.c.suspicious_clasfieds_id == clasfieds_offer_id
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            data = result.fetchone()
            return data

    async def add_suspicious_offer(self, suspicious_offer: SuspiciousOffer) -> None:
        ins = (
            insert(suspicious_offers)
            .values(
                suspicious_clasfieds_id=suspicious_offer.suspicious_clasfieds_id,
                is_suspicious=suspicious_offer.is_suspicious,
            )
            .on_conflict_do_nothing()
        )
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def select_suspicious_offers_from_labeling_data(self):
        subquery = select(labeling_data.c.vin).scalar_subquery()

        query = (
            select(
                offers_base.c.clasfieds_id,
                offers_base.c.title,
                offers_base.c.description,
                offers_details.c.model,
                offers_details.c.price,
                offers_details.c.milage,
                offers_details.c.condition,
                offers_details.c.country_origin,
            )
            .select_from(
                offers_base.join(
                    offers_details,
                    offers_base.c.clasfieds_id == offers_details.c.clasfieds_id,
                )
            )
            .where(offers_base.c.vin.in_(subquery))
        )

        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            data = result.fetchall()
            return data

    async def add_suspicious_offer_v2(self, suspicious_offer: SuspiciousOffer) -> None:
        ins = (
            insert(suspicious_offers_v2)
            .values(
                suspicious_clasfieds_id=suspicious_offer.suspicious_clasfieds_id,
                is_suspicious=suspicious_offer.is_suspicious,
            )
            .on_conflict_do_nothing()
        )
        async with self.engine.begin() as conn:
            await conn.execute(ins)

    async def select_all_suspicious_offers_v2(self):
        query = select(suspicious_offers_v2)
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            data = result.fetchall()
            return data

    async def select_single_suspicious_offer_v2(self, clasfieds_offer_id: int):
        query = select(suspicious_offers_v2).where(
            suspicious_offers.c.suspicious_clasfieds_id == clasfieds_offer_id
        )
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            data = result.fetchone()
            return data
