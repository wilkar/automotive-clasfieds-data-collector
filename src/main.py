import csv
import logging
from datetime import datetime

from src.config import log_init
from src.raw_offer_producer.bezwypadkowe_net import BezwypadkoweTrainingDataProducer
from src.raw_offer_producer.olx import OlxRawOfferProducer
from src.raw_offer_producer.otomoto import OtomotoRawOfferProducer

log_init.setup_logging()

logger = logging.getLogger(__name__)


# TODO: do full async implementation
async def process():
    olx_raw_offer_producer = OlxRawOfferProducer()
    training_data_producer = BezwypadkoweTrainingDataProducer()
    otomoto_raw_offer_producer = OtomotoRawOfferProducer()

    logger.info("Scraping labeling data")
    vins = list(training_data_producer.get_offers())

    logger.info("Scraping offer data from Olx data")
    olx_offers = list(olx_raw_offer_producer.get_offers())

    # logger.info("Scraping offer data from Otomoto")
    # otomoto_offers = list(otomoto_raw_offer_producer.get_offers())

    # offers = olx_offers + otomoto_offers
    offers = olx_offers

    # TODO: save offers to database
    logger.info("Saving labeling data")
    with open("labeling_data.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["VIN"])
        for vin in vins:
            writer.writerow([vin.vin])

    logger.info("Saving offer data")
    with open("offers.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "Brand",
                "Classifieds_ID",
                "Link",
                "Title",
                "Created_Time",
                "Description",
                "VIN",
                "Region",
                "City",
                "Model",
                "Price",
                "Engine_Size",
                "Manufactured_Year",
                "Petrol",
                "Car_Body",
                "Milage",
                "Color",
                "Condition",
                "Transmission",
                "Country_Origin",
                "Right_Hand_Drive",
            ]
        )
        for offer in offers:
            logger.info(f"Saving offer {offer.id}")
            datetime_object = datetime.fromisoformat(offer.created_time)
            datetime_object = datetime_object.replace(tzinfo=None)
            writer.writerow(
                [
                    offer.brand,
                    offer.id,
                    offer.link,
                    offer.title,
                    datetime_object,
                    offer.description,
                    offer.vin,
                    offer.location[0].region,
                    offer.location[0].city,
                    offer.parameters[0].model,
                    offer.parameters[0].price,
                    offer.parameters[0].engine_size,
                    offer.parameters[0].manufactured_year,
                    offer.parameters[0].petrol,
                    offer.parameters[0].car_body,
                    offer.parameters[0].milage,
                    offer.parameters[0].color,
                    offer.parameters[0].condition,
                    offer.parameters[0].transmission,
                    offer.parameters[0].country_origin,
                    offer.parameters[0].righthanddrive,
                ]
            )
