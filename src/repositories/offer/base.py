import datetime
from typing import Protocol


class OfferRepository(Protocol):
    async def add_base_offer_info(
        self,
        brand: str,
        clasfieds_id: int,
        link: str,
        title: str,
        created_time: str,
        description: str,
        image_link: str,
        vin: str,
        scraped_time: datetime.datetime,
    ) -> None:
        """Add basic offer information"""

    async def add_location_offer_info(
        self, clasfieds_id: str, region: str, city: str
    ) -> None:
        """Add location offer information"""

    async def add_params_offer_info(
        self,
        clasfieds_id: str,
        model: str,
        price: int,
        engine_size: int,
        manufactured_year: int,
        petrol: str,
        car_body: str,
        milage: int,
        color: str,
        condition: str,
        transmission: str,
        country_origin: str,
        righthanddrive: str,
    ) -> None:
        """Add all secondary offer details"""

    async def add_labeling_data(self, vin: str) -> None:
        """Add scraped labeling data"""
