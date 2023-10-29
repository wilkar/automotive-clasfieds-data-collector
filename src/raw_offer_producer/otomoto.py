import logging
from typing import Iterator

import requests
from dacite import from_dict

from src.config import log_init
from src.config.otomoto_config import (
    HEADERS,
    OTOMOTO_BRANDS,
    OTOMOTO_MAIN_PAGE,
    OTOMOTO_PAGINATION_LIMIT,
)
from src.models.raw_offer import RawOffer, RawOfferLocation, RawOfferParameters
from src.raw_offer_producer.base import BaseRawOfferProducer

log_init.setup_logging()

logger = logging.getLogger(__name__)


class OtomotoRawOfferProducer(BaseRawOfferProducer):
    def __init__(
        self,
        otomoto_brands: list = OTOMOTO_BRANDS,
        otomoto_pagination_limit: int = OTOMOTO_PAGINATION_LIMIT,
        headers: dict = HEADERS,
        otomoto_main_page=OTOMOTO_MAIN_PAGE,
    ):
        self.otomoto_brands = otomoto_brands
        self.otomoto_pagination_limit = otomoto_pagination_limit
        self.headers = headers
        self.otomoto_main_page = otomoto_main_page

    def _olx_api_url_builder(self, page: int, brand: str) -> str:
        return f"https://www.otomoto.pl/graphql?operationName=listingScreen&variables=%7B%22after%22%3Anull%2C%22click2BuyExperimentId%22%3A%22CARS-34184%22%2C%22click2BuyExperimentVariant%22%3A%22a%22%2C%22experiments%22%3A%5B%7B%22key%22%3A%22MCTA-900%22%2C%22variant%22%3A%22a%22%7D%2C%7B%22key%22%3A%22MCTA-1059%22%2C%22variant%22%3A%22a%22%7D%5D%2C%22filters%22%3A%5B%7B%22name%22%3A%22filter_enum_make%22%2C%22value%22%3A%22{brand}%22%7D%2C%7B%22name%22%3A%22category_id%22%2C%22value%22%3A%2229%22%7D%5D%2C%22includeClick2Buy%22%3Atrue%2C%22includeFiltersCounters%22%3Afalse%2C%22includePriceEvaluation%22%3Atrue%2C%22includePromotedAds%22%3Afalse%2C%22includeRatings%22%3Afalse%2C%22includeSortOptions%22%3Afalse%2C%22maxAge%22%3A60%2C%22page%22%3A{page}%2C%22parameters%22%3A%5B%22make%22%2C%22offer_type%22%2C%22fuel_type%22%2C%22gearbox%22%2C%22country_origin%22%2C%22mileage%22%2C%22engine_capacity%22%2C%22engine_code%22%2C%22engine_power%22%2C%22first_registration_year%22%2C%22model%22%2C%22version%22%2C%22year%22%5D%2C%22searchTerms%22%3Anull%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%229f5d49befb5eee8d53a70f5f135a7e8a209f2e8f8afb6d1a21e058fd4f97e62e%22%2C%22version%22%3A1%7D%7D"

    def _define_limits_for_brands(self, brand):
        response_data = self._get_response(self._olx_api_url_builder(1, brand))
        total_count = response_data["data"]["advertSearch"]["totalCount"]
        return total_count

    # TODO: handle duplicates
    def get_offers(self) -> Iterator[RawOffer]:
        for brand in self.otomoto_brands:
            for offer in self._get_all_offers_from_brand(brand):
                yield self._map_offers(offer)

    def _get_response(self, url: str) -> dict:
        data = requests.get(url)
        data.raise_for_status()
        return data.json()

    def _get_offers_for_category_with_page(self, page, brand) -> list:
        category_url = self._olx_api_url_builder(page, brand)
        olx_json = self._get_response(category_url)
        return olx_json["data"]["advertSearch"]["edges"]

    def _get_all_offers_from_brand(self, brand) -> list[dict]:
        all_brand_offers: list = []
        pagination_limit = self._define_limits_for_brands(brand) // 32
        for page in range(pagination_limit):
            offers = self._get_offers_for_category_with_page(page, brand)
            for offer in offers:
                all_brand_offers.append(offer)
        logger.info(f"Found {len(all_brand_offers)} in category_id: {brand}")
        return all_brand_offers

    def _map_offers(self, offer: dict) -> RawOffer:
        brand = offer.get("node", {}).get("title", "").split()[0]
        content = offer.get("node", {})

        return RawOffer(
            brand=brand,
            id=content.get("id", ""),
            link=content.get("url", ""),
            created_time=content.get("createdAt", ""),
            description=content.get("shortDescription", ""),
            title=content.get("title", ""),
            image_links=self._get_images_list(content),
            parameters=[self._get_offer_parameters(content)],
            location=[self._get_location(content)],
            vin=None
            # vin= fetch vin from product page
        )

    def _get_vin_from_product_page(self, url):
        content = self._get_response(url)
        pass

    def _get_location(self, offer: dict) -> RawOfferLocation:
        region = offer.get("location", {}).get("region", {}).get("name", None)
        city = offer.get("location", {}).get("city", {}).get("name", None)
        return RawOfferLocation(region=region, city=city)

    def _get_images_list(self, offer) -> list[str]:
        return [offer.get("thumbnail", {}).get("x1", None)]

    def _get_offer_parameters(self, offer: dict) -> RawOfferParameters:
        params = {
            param.get("key", ""): param.get("value", {})
            for param in offer.get("parameters", [])
        }
        params_defaults = {
            key: params.get(key, None)
            for key in RawOfferParameters.__annotations__.keys()
        }
        return from_dict(data_class=RawOfferParameters, data=params_defaults)
