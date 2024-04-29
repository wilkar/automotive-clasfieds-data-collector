import asyncio
import logging
import re

from sqlalchemy import Row

from src.config import log_init
from src.models.raw_offer import SuspiciousOffer
from src.repositories.helpers import get_engine
from src.repositories.offer.sql_alchemy import SqlAlchemyOfferRepository

log_init.setup_logging()

logger = logging.getLogger(__name__)


async def _is_suspicious(offer: Row) -> bool:
    vin = offer.vin

    if vin is None:
        return True

    if re.match(r"^([a-zA-Z0-9])\1{16}$", vin):
        return True

    if vin.lower() == vin or vin.upper() == vin:
        if re.match(r"^([a-zA-Z0-9])\1+$", vin):
            return True

    placeholder_patterns = [
        "zapytaj",
        "wysylam",
        "kontakt",
        "zadzwon",
        "nrvin",
        "astaz",
        "error",
        "xxxx",
        "vvvv",
        "zzzz",
        "yyyy",
        "www",
    ]

    if any(re.search(pattern, vin.lower()) for pattern in placeholder_patterns):
        return True

    if re.search("[^a-hj-npr-z0-9]", vin.lower()):
        return True

    if re.match(r"^123456789|abcdefg|012345|987654|abcdef", vin.lower()):
        return True

    if re.search(r"tel|phone|contact|zadzwon", vin.lower()):
        return True

    if re.match(r"^(wauzzz|vf|wba)[a-z0-9]*[x]{5,}", vin.lower()):
        return True

    return False


async def process_offers():
    engine = get_engine()
    scraped_offer_repository = SqlAlchemyOfferRepository(engine)

    all_offers = await scraped_offer_repository.select_all_offers()
    for offer in all_offers:
        suspicious_indicator = await _is_suspicious(offer)
        suspicious_offer = SuspiciousOffer(
            suspicious_clasfieds_id=offer.clasfieds_id,
            is_suspicious=suspicious_indicator,
        )
        await scraped_offer_repository.add_suspicious_offer(suspicious_offer)


asyncio.run(process_offers())
