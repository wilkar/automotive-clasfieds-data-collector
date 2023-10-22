from unittest.mock import Mock, patch

import pytest
from requests.exceptions import HTTPError

from src.models.raw_offer import RawOffer, RawOfferLocation, RawOfferParameters
from src.raw_offer_producer.olx import OlxRawOfferProducer


def test_olx_api_url_builder():
    producer = OlxRawOfferProducer()
    page = 1
    category_id = 181
    built_url = producer._olx_api_url_builder(page, category_id)
    assert (
        built_url
        == "https://www.olx.pl/api/v1/offers/?offset=40&limit=50&category_id=181"
    )


@patch("src.raw_offer_producer.olx.requests.get")
def test_get_response(mock_get):
    mock_response = Mock()
    expected_dict = {"key": "value"}
    mock_response.json.return_value = expected_dict
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    producer = OlxRawOfferProducer()
    result = producer._get_response("dummy_url")

    assert result == expected_dict
    mock_response.raise_for_status.assert_called_once()


@patch("src.raw_offer_producer.olx.requests.get")
def test_get_response_failed_request(mock_get):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPError()
    mock_get.return_value = mock_response

    producer = OlxRawOfferProducer()
    with pytest.raises(HTTPError):
        producer._get_response("dummy_url")


def test_map_offers():
    producer = OlxRawOfferProducer()
    sample_offer = {
        "id": "123",
        "title": "TestTitle BrandOtherInfo",
        "description": "A\ndescription\nwith\nnewlines.",
        "url": "http://test.com",
        "created_time": None,
        "photos": [{"link": "http://image1.com"}, {"link": "http://image2.com"}],
        "location": {"region": {"name": "TestRegion"}, "city": {"name": "TestCity"}},
        "params": [{"key": "vin", "value": {"label": "TestVin"}}],
    }

    mapped_offer = producer._map_offers(sample_offer)

    parameters = RawOfferParameters(
        model=None,
        price=None,
        engine_size=None,
        manufactured_year=None,
        engine_power=None,
        petrol=None,
        car_body=None,
        milage=None,
        color=None,
        condition=None,
        transmission=None,
        drive=None,
        country_origin=None,
        righthanddrive=None,
        vin="TestVin",
    )

    assert mapped_offer == RawOffer(
        brand="TestTitle",
        id="123",
        link="http://test.com",
        created_time=None,
        description="A description with newlines.",
        title="TestTitle BrandOtherInfo",
        image_links=["http://image1.com", "http://image2.com"],
        parameters=[parameters],
        location=[RawOfferLocation(region="TestRegion", city="TestCity")],
        vin="TestVin",
    )
