import asyncio

from sentence_transformers import SentenceTransformer  # type: ignore
from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

from src.models.raw_offer import SuspiciousOffer
from src.repositories.helpers import get_engine
from src.repositories.offer.sql_alchemy import SqlAlchemyOfferRepository


class TestSusSelector:
    def __init__(self):
        self.engine = get_engine()
        self.scraped_offer_repository = SqlAlchemyOfferRepository(self.engine)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    async def _get_suspicions_descriptions(self):
        suspicious_offers = (
            await self.scraped_offer_repository.select_suspicious_offers_from_labeling_data()
        )
        suspicious_data = [(offer[0], offer[2]) for offer in suspicious_offers]
        suspicious_descriptions = [data[1] for data in suspicious_data]
        return suspicious_data, self.model.encode(suspicious_descriptions)

    async def get_similar_descriptions(self, similarity_threshold=0.8) -> None:
        (
            suspicious_data,
            suspicious_embeddings,
        ) = await self._get_suspicions_descriptions()
        offers = await self.scraped_offer_repository.select_all_offers()
        offers_data = [(offer[0], offer[2]) for offer in offers]
        descriptions = [offer[1] for offer in offers_data]
        embeddings = self.model.encode(descriptions)
        suspicious_offers: list = []

        for i, (suspicious_id, suspicious_embedding) in enumerate(
            zip(suspicious_data, suspicious_embeddings)
        ):
            similarities = cosine_similarity([suspicious_embedding], embeddings)[  # type: ignore
                0
            ]
            for index, similarity_score in enumerate(similarities):
                if similarity_score > similarity_threshold:
                    suspicious_offers.append(offers_data[index][0])

        await self._populate_suspicious_offers_v2(suspicious_offers)

    async def _populate_suspicious_offers_v2(self, suspicious_offers: list):
        offers = await self.scraped_offer_repository.select_all_offers()

        for offer in offers:
            suspicious_indicator: bool = False
            if offer.clasfieds_id in suspicious_offers:
                suspicious_indicator = True
            suspicious_offer = SuspiciousOffer(
                suspicious_clasfieds_id=offer.clasfieds_id,
                is_suspicious=suspicious_indicator,
            )
            await self.scraped_offer_repository.add_suspicious_offer_v2(
                suspicious_offer
            )


if __name__ == "__main__":
    test = TestSusSelector()

    asyncio.run(test.get_similar_descriptions())
