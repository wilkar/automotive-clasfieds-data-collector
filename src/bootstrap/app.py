from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from src.config.bezwypadkowe_net_config import (BEZWYPADKOWE_MAIN_URL,
                                                BEZWYPADKOWE_STARTING_POINT)
from src.config.olx_config import (OLX_API_LIMIT, OLX_API_OFFSET,
                                   OLX_API_PAGINATION_LIMIT, OLX_API_URL,
                                   OLX_CATEGORIES)
from src.raw_offer_producer.base import BaseRawOfferProducer
from src.raw_offer_producer.bezwypadkowe_net import \
    BezwypadkoweTrainingDataProducer
from src.raw_offer_producer.olx import OlxRawOfferProducer
from src.raw_offer_producer.otomoto import OtomotoRawOfferProducer
from src.repositories.helpers import get_engine
from src.repositories.offer.sql_alchemy import SqlAlchemyOfferRepository


@dataclass
class AppContainer:
    olx_raw_offer_producer: BaseRawOfferProducer
    otomoto_raw_offer_producer: BaseRawOfferProducer
    get_training_data_raw_offer_producer: BaseRawOfferProducer
    scraped_offer_repository: SqlAlchemyOfferRepository


def build_app_container() -> AppContainer:
    engine = get_engine()
    return AppContainer(
        olx_raw_offer_producer=get_olx_raw_offer_producer(),
        otomoto_raw_offer_producer=get_otomoto_raw_offer_producer(),
        get_training_data_raw_offer_producer=get_training_data_raw_offer_producer(),
        scraped_offer_repository=get_scraped_offer_repository(engine),
    )


def get_olx_raw_offer_producer() -> BaseRawOfferProducer:
    return OlxRawOfferProducer(
        olx_api_limit=OLX_API_LIMIT,
        olx_api_offset=OLX_API_OFFSET,
        olx_api_pagination_limit=OLX_API_PAGINATION_LIMIT,
        olx_api_url=OLX_API_URL,
        olx_categories=OLX_CATEGORIES,
    )


def get_otomoto_raw_offer_producer() -> BaseRawOfferProducer:
    return OtomotoRawOfferProducer(
        olx_api_limit=OLX_API_LIMIT,
        olx_api_offset=OLX_API_OFFSET,
        olx_api_pagination_limit=OLX_API_PAGINATION_LIMIT,
        olx_api_url=OLX_API_URL,
        olx_categories=OLX_CATEGORIES,
    )


def get_training_data_raw_offer_producer() -> BaseRawOfferProducer:
    return BezwypadkoweTrainingDataProducer(
        bezwypadkowe_main_url=BEZWYPADKOWE_MAIN_URL,
        bezwypadkowe_starting_point=BEZWYPADKOWE_STARTING_POINT,
    )


def get_scraped_offer_repository(engine: AsyncEngine) -> SqlAlchemyOfferRepository:
    return SqlAlchemyOfferRepository(engine)
