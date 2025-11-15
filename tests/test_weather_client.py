import time
from unittest.mock import Mock

import pytest

from app import WeatherClient


class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json


def test_get_weather_success_and_cache(monkeypatch):
    sample = {
        "main": {"temp": 70.0, "feels_like": 69.5, "temp_min": 65.0, "temp_max": 75.0},
        "weather": [{"description": "clear sky", "icon": "01d"}],
        "name": "Testville"
    }

    # Create a client with short TTL so test runs fast
    client = WeatherClient(api_key="testkey", ttl=2)

    # Patch the session.get to return our DummyResponse
    dummy = DummyResponse(sample, status_code=200)
    mock_get = Mock(return_value=dummy)
    client.session.get = mock_get

    # First call should hit the underlying session.get
    data1 = client.get_weather("12345")
    assert data1 is not None
    assert data1["name"] == "Testville"
    assert mock_get.call_count == 1

    # Second call within TTL should return cached result and not call session.get again
    data2 = client.get_weather("12345")
    assert data2 is data1
    assert mock_get.call_count == 1

    # After TTL expiry should call session.get again
    time.sleep(2.1)
    data3 = client.get_weather("12345")
    assert mock_get.call_count == 2
    assert data3 is not None


def test_get_weather_invalid_payload(monkeypatch):
    client = WeatherClient(api_key="testkey")
    # Return invalid json payload (missing 'main')
    dummy = DummyResponse({"foo": "bar"}, status_code=200)
    client.session.get = Mock(return_value=dummy)

    assert client.get_weather("99999") is None
