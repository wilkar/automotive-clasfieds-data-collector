import pytest
import requests
import requests_mock

from src.raw_offer_producer.otomoto import OtomotoRawOfferProducer


def test_get_response():
    url = "http://example.com"
    mock_response = {"key": "value"}

    with requests_mock.Mocker() as m:
        m.get(url, json=mock_response)
        producer = OtomotoRawOfferProducer()
        response = producer._get_response(url)

    assert response == mock_response


def test_get_response_error():
    url = "http://example.com"

    with requests_mock.Mocker() as m:
        m.get(url, status_code=500)
        producer = OtomotoRawOfferProducer()

        with pytest.raises(requests.exceptions.HTTPError):
            producer._get_response(url)
