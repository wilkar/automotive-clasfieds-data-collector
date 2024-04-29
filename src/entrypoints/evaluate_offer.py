import asyncio
import logging

from src.config import log_init
from src.services.suspiciousness_predictor import (
    SuspiciousnessPredictor,
    ml_model,
    mode,
)
from src.evaluate_offers_library import fraulent_offers, non_fraulent_offers

log_init.setup_logging()

logger = logging.getLogger(__name__)


async def process(offers: list[dict], ml_model: ml_model, mode: mode):
    for offer in offers:
        evaluator = SuspiciousnessPredictor(offer, ml_model, mode)
        prediction = evaluator.predict_suspiciousness()
        logger.info(f'Prediction for offer {offer["clasfieds_id"]}: {prediction}')


async def main():
    logger.info("Running...")
    for model in ml_model:
        logger.info(f"Processing fraulent offers with description based model {model}")
        await process(fraulent_offers, model, mode.manual)
        logger.info(
            f"Processing non-fraulent offers with description based model {model}"
        )
        await process(non_fraulent_offers, model, mode.manual)

        logger.info(f"Processing fraulent offers with VIN based model {model}")
        await process(fraulent_offers, model, mode.vin)
        logger.info(f"Processing non-fraulent offers with VIN based model {model}")
        await process(non_fraulent_offers, model, mode.vin)

    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
