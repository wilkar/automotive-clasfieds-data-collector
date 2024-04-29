import logging
from datetime import datetime, timezone
from typing import Iterator

import requests
from dacite import from_dict

from src.config import log_init
from src.config.olx_config import (
    OLX_API_LIMIT,
    OLX_API_OFFSET,
    OLX_API_PAGINATION_LIMIT,
    OLX_API_URL,
    OLX_CATEGORIES,
)
from src.models.raw_offer import RawOffer, RawOfferLocation, RawOfferParameters
from src.raw_offer_producer.base import BaseRawOfferProducer

log_init.setup_logging()

logger = logging.getLogger(__name__)


class OlxRawOfferProducer(BaseRawOfferProducer):
    def __init__(
        self,
        olx_categories: dict = OLX_CATEGORIES,
        olx_api_url: str = OLX_API_URL,
        olx_api_limit: int = OLX_API_LIMIT,
        olx_api_pagination_limit: int = OLX_API_PAGINATION_LIMIT,
        olx_api_offset: int = OLX_API_OFFSET,
    ):
        self.olx_categories = olx_categories
        self.olx_api_url = olx_api_url
        self.olx_api_limit = olx_api_limit
        self.olx_api_pagination_limit = olx_api_pagination_limit
        self.olx_api_offset = olx_api_offset

    # TODO: handle duplicates
    def get_offers(self) -> Iterator[RawOffer]:
        for category in self.olx_categories.items():
            for offer in self._get_all_offers_from_category(category):
                yield self._map_offers(offer)

    def _olx_api_url_builder(self, page: int, category_id: int) -> str:
        offset = page * self.olx_api_offset
        url = f"{self.olx_api_url}?offset={offset}&limit={self.olx_api_limit}&category_id={category_id}&sort_by=created_at:desc"
        return url

    def _get_response(self, url: str) -> dict:
        data = requests.get(url)
        data.raise_for_status()
        return data.json()

    def _get_offers_for_category_with_page(self, page, category_id) -> list:
        category_url = self._olx_api_url_builder(page, category_id)
        olx_json = self._get_response(category_url)
        return olx_json["data"]

    def _get_all_offers_from_category(self, category: tuple) -> list:
        all_category_offers: list = []
        pagination_limit = self.olx_api_pagination_limit
        for page in range(pagination_limit):
            offers = self._get_offers_for_category_with_page(page, category[0])
            for offer in offers:
                all_category_offers.append(offer)
        logger.info(f"Found {len(all_category_offers)} in category_id: {category[1]}")
        return all_category_offers

    def _get_location(self, offer) -> RawOfferLocation:
        region = offer.get("location", {}).get("region", {}).get("name", "")
        city = offer.get("location", {}).get("city", {}).get("name", "")
        id = offer.get("id", "")
        return RawOfferLocation(id=id, region=region, city=city)

    def _get_images_list(self, offer) -> list[str]:
        return [image.get("link", "") for image in offer.get("photos", [])]

    def _map_offers(self, offer: dict) -> RawOffer:
        brand = offer.get("title", "").split()[0]
        parameters = self._get_offer_parameters(offer)
        return RawOffer(
            brand=brand,
            id=offer.get("id", ""),
            link=offer.get("url", ""),
            created_time=offer.get("created_time"),
            description=offer.get("description", "")
            .replace("\n", " ")
            .replace("\r", ""),
            title=offer.get("title", ""),
            image_links=self._get_images_list(offer),
            parameters=[parameters],
            location=[self._get_location(offer)],
            vin=str(parameters.vin).strip(),
            scraped_time=datetime.now(timezone.utc),
        )

    def _get_offer_parameters(self, offer: dict) -> RawOfferParameters:
        params = {
            param.get("key", ""): param.get("value", {}).get("label", "")
            for param in offer.get("params", [])
        }
        offer_id = offer.get("id", 0)

        if "price" in params:
            params["price"] = self.parse_price_to_int(params["price"])

        if "milage" in params:
            params["milage"] = self.parse_milage_to_int(params["milage"])

        params_defaults = {
            key: params.get(key, None)
            for key in RawOfferParameters.__annotations__.keys()
        }
        params_defaults["id"] = offer_id

        return from_dict(data_class=RawOfferParameters, data=params_defaults)

    def parse_price_to_int(self, price_str: str) -> int | None:
        price_str_cleaned = (
            price_str.replace("zł", "").replace(" ", "").replace(",", "")
        )
        try:
            return int(price_str_cleaned)
        except ValueError:
            return None

    def parse_milage_to_int(self, milage_str: str) -> int | None:
        if milage_str is None:
            return None
        milage_str_cleaned = (
            milage_str.replace("km", "").replace(" ", "").replace(",", "")
        )
        try:
            return int(milage_str_cleaned)
        except ValueError:
            return None
