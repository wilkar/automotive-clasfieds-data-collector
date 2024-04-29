import logging
import re
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from src.config import log_init
from src.config.bezwypadkowe_net_config import (
    BEZWYPADKOWE_MAIN_URL,
    BEZWYPADKOWE_STARTING_POINT,
)
from src.models.labeling import TrainingData
from src.raw_offer_producer.base import BaseRawOfferProducer

log_init.setup_logging()

logger = logging.getLogger(__name__)


class BezwypadkoweTrainingDataProducer(BaseRawOfferProducer):
    def __init__(
        self,
        bezwypadkowe_main_url: str = BEZWYPADKOWE_MAIN_URL,
        bezwypadkowe_starting_point: str = BEZWYPADKOWE_STARTING_POINT,
    ):
        self.bezwypadkowe_main_url = bezwypadkowe_main_url
        self.bezwypadkowe_starting_point = bezwypadkowe_starting_point

    def _get_response(self, url) -> BeautifulSoup:
        try:
            data = requests.get(url)
            data.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch data from {url}: {e}")
            raise
        return BeautifulSoup(data.content, "html.parser")

    def _url_builder(self, relative_url) -> str:
        return self.bezwypadkowe_main_url + relative_url

    def _get_brands(self) -> list[str]:
        main = self._get_response(self.bezwypadkowe_starting_point)
        brands: list[str] = [
            element.find("a", href=True)["href"]
            for element in main.find_all("h2", {"class": "forumtitle"})
        ]
        return brands

    def _get_pagination_urls(self, url) -> list[str]:
        content = str(self._get_response(url))
        links: list = []
        match = re.search(r"Strona \d+ z (\d+)", content)
        if match is not None:
            pages = int(match.group(1))
        else:
            pages = 1
        for page in range(pages):
            page = page + 1
            pagination_url = f"{url}/page{page}"
            links.append(pagination_url)
        return links

    def _get_vins(self, container: list) -> list[str]:
        vins: list[str] = [
            match.group(1)
            for item in container
            if (match := re.search(r"\s([A-Za-z0-9]{17})[\s<]", str(item))) is not None
        ]
        return vins

    def get_offers(self) -> Iterator[TrainingData]:
        for brand in self._get_brands():
            brand_name_match = re.search(r"forumdisplay\.php/\d{1,3}-(.*?)\?", brand)
            assert brand_name_match
            logger.info(f"Parsing brand {brand_name_match.group(1)}")
            for brand_link in self._get_pagination_urls(self._url_builder(brand)):
                content = self._get_response(brand_link)
                container = content.find_all("a", {"class": "title"})
                for vin in self._get_vins(container):
                    yield TrainingData(vin=vin)
