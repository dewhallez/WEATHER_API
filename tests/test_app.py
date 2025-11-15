from unittest.mock import Mock

import pytest

from app import app as flask_app, weather_client


@pytest.fixture
def client(monkeypatch):
    # Ensure the app has a test config API key
    flask_app.config['TESTING'] = True
    flask_app.config['OPENWEATHER_API_KEY'] = 'testkey'
    # Patch weather_client.get_weather to avoid real HTTP calls
    sample = {
        "main": {"temp": 50.0, "feels_like": 49.0, "temp_min": 45.0, "temp_max": 55.0},
        "weather": [{"description": "light rain", "icon": "10d"}],
        "name": "MockCity"
    }
    monkeypatch.setattr(weather_client, 'get_weather', Mock(return_value=sample))

    with flask_app.test_client() as client:
        yield client


def test_results_route_success(client):
    rv = client.post('/results', data={'zipCode': '10001'})
    assert rv.status_code == 200
    text = rv.get_data(as_text=True)
    assert 'MockCity' in text
    assert '° F' in text


def test_results_route_missing_zip(client):
    rv = client.post('/results', data={'zipCode': ''})
    assert rv.status_code == 200
    assert 'Please enter a zip code' in rv.get_data(as_text=True)
