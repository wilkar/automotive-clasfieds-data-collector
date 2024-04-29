from src.repositories.helpers import get_engine
from src.repositories.offer.sql_alchemy import SqlAlchemyOfferRepository


class DataSetBuilder:
    def __init__(self):
        self.engine = get_engine()
        self.scraped_offer_repository = SqlAlchemyOfferRepository(self.engine)

    async def _prepare_dataset_with_suspicious_vin_numbers(self) -> list[dict]:
        all_offers = await self.scraped_offer_repository.select_all_offers()
        all_suspicious = (
            await self.scraped_offer_repository.select_all_suspicious_offers()
        )
        suspicious_dict = {
            offer.suspicious_clasfieds_id: offer.is_suspicious
            for offer in all_suspicious
        }

        dataset: list = []
        for offer in all_offers:
            is_suspicious = suspicious_dict.get(offer.clasfieds_id, False)
            dataset.append(
                {
                    "title": offer[1],
                    "description": offer[2],
                    "vin": offer[3],
                    "model": offer[4],
                    "price": offer[5],
                    "milage": offer[6],
                    "condition": offer[7],
                    "country_origin": offer[8],
                    "is_suspicious": is_suspicious,
                }
            )

        return dataset

    async def _prepare_dataset_with_manually_labeled_offers(self) -> list[dict]:
        all_offers = await self.scraped_offer_repository.select_all_offers()
        all_suspicious = (
            await self.scraped_offer_repository.select_all_suspicious_offers_v2()
        )
        suspicious_dict = {
            offer.suspicious_clasfieds_id: offer.is_suspicious
            for offer in all_suspicious
        }

        dataset: list = []
        for offer in all_offers:
            is_suspicious = suspicious_dict.get(offer.clasfieds_id, False)
            dataset.append(
                {
                    "title": offer[1],
                    "description": offer[2],
                    "vin": offer[3],
                    "model": offer[4],
                    "price": offer[5],
                    "milage": offer[6],
                    "condition": offer[7],
                    "country_origin": offer[8],
                    "is_suspicious": is_suspicious,
                }
            )

        return dataset
