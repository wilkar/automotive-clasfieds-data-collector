import asyncio
import logging


from src.services.models_generator import ModelsGenerator
import asyncio
import logging

from sklearn.ensemble import (
    AdaBoostClassifier,  # type: ignore
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression  # type: ignore
from sklearn.neighbors import KNeighborsClassifier  # type: ignore

from src.config import log_init

log_init.setup_logging()

logger = logging.getLogger(__name__)

models = {
    "LogisticRegression": LogisticRegression(),
    "RandomForestClassifier": RandomForestClassifier(),
    "GradientBoostingClassifier": GradientBoostingClassifier(),
    "AdaBoostClassifier": AdaBoostClassifier(),
    "ExtraTreesClassifier": ExtraTreesClassifier(),
    "KNeighborsClassifier": KNeighborsClassifier(),
}


async def process():
    test = ModelsGenerator(models)
    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(test.evaluate_models_with_manually_labeled_offers()),
        loop.create_task(test.evaluate_models_with_suspicious_vin_numbers()),
    ]
    results = loop.run_until_complete(asyncio.gather(*tasks))

    for result in results:
        print(result)


async def main():
    logger.info("Running...")
    await process()
    logger.info("Done!")


if __name__ == "__main__":
    asyncio.run(main())
