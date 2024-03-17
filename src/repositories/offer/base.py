from typing import Protocol

from src.models.raw_offer import RawOffer, RawOfferLocation, RawOfferParameters


class OfferRepository(Protocol):
    async def add_base_offer_info(self, raw_offer: RawOffer) -> None:
        """Add basic offer information"""

    async def add_location_offer_info(
        self, raw_offer_location: RawOfferLocation
    ) -> None:
        """Add location offer information"""

    async def add_params_offer_info(self, offer_parameters: RawOfferParameters) -> None:
        """Add all secondary offer details"""

    async def add_labeling_data(self, vin: str) -> None:
        """Add scraped labeling data"""
