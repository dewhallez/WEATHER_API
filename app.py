import os
import time
import logging
import configparser
from flask import Flask, render_template, request
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    # Optional: allow local .env files for development
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; continue if not installed
    pass


# Configure app and logger
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
app.logger = logging.getLogger('weather_api')
app.logger.setLevel(logging.INFO)


def _load_api_key_from_config():
    cfg = configparser.ConfigParser()
    cfg_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    try:
        cfg.read(cfg_path)
        return cfg.get('openweathermap', 'api', fallback='').strip()
    except Exception:
        return ''


# Prefer environment variable, fallback to config.ini for backward-compatibility
_api_key = os.environ.get('OPENWEATHER_API_KEY') or _load_api_key_from_config()
app.config['OPENWEATHER_API_KEY'] = _api_key


class WeatherClient:
    """Small helper to call OpenWeather with a shared Session, retries, timeouts and a TTL cache.

    - Uses requests.Session with HTTPAdapter Retry to reduce transient failures.
    - Keeps a small in-memory TTL cache to reduce repeated identical requests.
    """

    def __init__(self, api_key: str, ttl: int = 600, max_cache_items: int = 500):
        self.api_key = api_key
        self.ttl = int(ttl)
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(['GET'])
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        # simple dict-based cache: key -> (expiry_timestamp, data)
        self._cache = {}
        self._max_cache_items = int(max_cache_items)

    def _make_cache_key(self, zip_code: str):
        return f"zip:{zip_code}:units:imperial"

    def get_weather(self, zip_code: str):
        if not zip_code:
            raise ValueError('zip_code is required')

        key = self._make_cache_key(zip_code)
        now = time.time()
        # Return cached if valid
        entry = self._cache.get(key)
        if entry:
            expiry, data = entry
            if expiry > now:
                app.logger.info('Cache hit for %s', zip_code)
                return data
            else:
                # expired
                self._cache.pop(key, None)

        # Build URL and call API with timeout
        api_url = f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code}&units=imperial&appid={self.api_key}"
        try:
            resp = self.session.get(api_url, timeout=(3, 7))
            resp.raise_for_status()
            data = resp.json()
            # basic validity checks
            if not isinstance(data, dict) or 'main' not in data or 'weather' not in data:
                app.logger.error('OpenWeather returned unexpected payload for %s: %s', zip_code, data)
                return None

            # Maintain simple cache size bound
            if len(self._cache) >= self._max_cache_items:
                # drop oldest entry (not strictly LRU, but simple)
                oldest = min(self._cache.items(), key=lambda it: it[1][0])
                self._cache.pop(oldest[0], None)

            self._cache[key] = (now + self.ttl, data)
            app.logger.info('Fetched weather for %s (cached for %s secs)', zip_code, self.ttl)
            return data
        except requests.RequestException as exc:
            app.logger.error('Weather API request failed for %s: %s', zip_code, exc)
            return None


# Instantiate the client (safe to do at import time)
weather_client = WeatherClient(app.config.get('OPENWEATHER_API_KEY') or '')


@app.route('/')
def weather_dashboard():
    return render_template('home.html')


@app.route('/results', methods=['POST'])
def render_results():
    zip_code = request.form.get('zipCode', '').strip()
    if not zip_code:
        return render_template('home.html', error='Please enter a zip code')

    api_key = app.config.get('OPENWEATHER_API_KEY')
    if not api_key:
        app.logger.error('OpenWeather API key missing')
        return render_template('home.html', error='Server configuration error: API key missing')

    data = weather_client.get_weather(zip_code)
    if not data:
        return render_template('home.html', error='Could not retrieve weather for that zip code. Please check the zip code and try again.')

    try:
        temp = "{0:.1f}".format(data['main']["temp"])
        feels_like = "{0:.1f}".format(data["main"]["feels_like"])
        location = data.get("name", 'Unknown location')
        weather = data['weather'][0]
        description = weather.get('description', '')
        icon = weather.get('icon', '')
        temp_min = "{0:.1f}".format(data["main"]["temp_min"])
        temp_max = "{0:.1f}".format(data["main"]["temp_max"])
    except (KeyError, IndexError, TypeError) as e:
        app.logger.error('Unexpected API response structure: %s', e)
        return render_template('home.html', error='Unexpected response from weather service.')

    return render_template('results.html', location=location, temp=temp, feels_like=feels_like, description=description, icon=icon, temp_min=temp_min, temp_max=temp_max)


if __name__ == '__main__':
    # Development server; for production use a WSGI server (gunicorn)
    app.run(debug=True)
