import logging
from datetime import datetime, timezone

from src.config import log_init
from src.models.labeling import TrainingData
from src.models.raw_offer import RawOffer, RawOfferLocation, RawOfferParameters
from src.raw_offer_producer.bezwypadkowe_net import \
    BezwypadkoweTrainingDataProducer
from src.raw_offer_producer.olx import OlxRawOfferProducer
from src.raw_offer_producer.otomoto import OtomotoRawOfferProducer
from src.repositories.helpers import get_engine
from src.repositories.offer.sql_alchemy import SqlAlchemyOfferRepository

log_init.setup_logging()

logger = logging.getLogger(__name__)


async def map_offer_data(
    offer: RawOffer,
) -> tuple[RawOffer, RawOfferParameters, RawOfferLocation]:
    offer_location = RawOfferLocation(
        id=offer.id,
        region=offer.location[0].region,
        city=offer.location[0].city,
    )

    offer_parameters = RawOfferParameters(
        id=offer.id,
        model=offer.parameters[0].model,
        price=offer.parameters[0].price,
        engine_size=offer.parameters[0].engine_size,
        manufactured_year=offer.parameters[0].manufactured_year,
        engine_power=offer.parameters[0].engine_power,
        petrol=offer.parameters[0].petrol,
        car_body=offer.parameters[0].car_body,
        milage=offer.parameters[0].milage,
        color=offer.parameters[0].color,
        condition=offer.parameters[0].condition,
        transmission=offer.parameters[0].transmission,
        drive=offer.parameters[0].drive,
        country_origin=offer.parameters[0].country_origin,
        righthanddrive=offer.parameters[0].righthanddrive,
        vin=offer.parameters[0].vin,
    )

    raw_offer = RawOffer(
        brand=offer.brand,
        id=offer.id,
        link=offer.link,
        title=offer.title,
        created_time=offer.created_time,
        description=offer.description,
        image_links=offer.image_links,
        vin=offer.vin,
        scraped_time=offer.created_time,
    )
    return raw_offer, offer_parameters, offer_location


async def upsert_olx_otomoto_data(
    offer: RawOffer, scraped_offer_repository: SqlAlchemyOfferRepository
):
    raw_offer, offer_parameters, offer_location = await map_offer_data(offer=offer)
    await scraped_offer_repository.add_base_offer_info(raw_offer)
    await scraped_offer_repository.add_location_offer_info(offer_location)
    await scraped_offer_repository.add_params_offer_info(offer_parameters)


async def upsert_labeling_data(
    offer: TrainingData, scraped_offer_repository: SqlAlchemyOfferRepository
):
    assert offer.vin
    is_present = await scraped_offer_repository.select_labeling_data(offer.vin)
    if not is_present:
        await scraped_offer_repository.add_labeling_data(vin=offer.vin)


async def process():
    engine = get_engine()
    scraped_offer_repository = SqlAlchemyOfferRepository(engine)
    olx_raw_offer_producer = OlxRawOfferProducer()
    training_data_producer = BezwypadkoweTrainingDataProducer()
    otomoto_raw_offer_producer = OtomotoRawOfferProducer()

    logger.info("Scraping labeling data from BEZWYPADKOWE.NET")
    vins = list(training_data_producer.get_offers())

    for vin in vins:
        await upsert_labeling_data(vin, scraped_offer_repository)

    logger.info("Scraping offer data from OLX data")
    olx_offers = list(olx_raw_offer_producer.get_offers())

    for offer in olx_offers:
        await upsert_olx_otomoto_data(offer, scraped_offer_repository)

    logger.info("Scraping offer data from OTOMOTO")
    otomoto_offers = list(otomoto_raw_offer_producer.get_offers())

    for offer in otomoto_offers:
        await upsert_olx_otomoto_data(offer, scraped_offer_repository)
