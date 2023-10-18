from abc import ABC, abstractmethod
from typing import Iterator

from src.models.labeling import TrainingData
from src.models.raw_offer import RawOffer


class BaseRawOfferProducer(ABC):
    @abstractmethod
    def get_offers(self) -> Iterator[RawOffer | TrainingData]:
        ...
