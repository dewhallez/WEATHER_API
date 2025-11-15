# Flask Weather App

A small Flask application that looks up current weather from OpenWeatherMap by US ZIP code.

Features added:
- Reads OpenWeather API key from the environment variable `OPENWEATHER_API_KEY` (recommended).
- Optional local `.env` support for development via `python-dotenv`.
- `WeatherClient` using a shared requests Session with retries, timeouts and a small in-memory TTL cache.
- Unit tests (pytest) and a GitHub Actions CI workflow that runs linting and tests on PRs.

## Quick start

1. Create and activate a virtual environment (macOS/Linux):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure your OpenWeather API key (one of):

- Preferred: create a `.env` file from the provided example and add your key:

```bash
cp .env.example .env
# edit .env and set OPENWEATHER_API_KEY=your_real_key
```

- Or copy the example ini and add your key (legacy):

```bash
cp config.example.ini config.ini
# edit config.ini and set the api value
```

3. Run the app locally (development server):

```bash
# For flask CLI
export FLASK_APP=app.py
export FLASK_ENV=development
flask run

# Or directly with python
python app.py
```

Open http://127.0.0.1:5000 in your browser and submit a US ZIP code.

## Tests and linting

Run tests and lint locally:

```bash
pytest -q
flake8 .
```

Unit tests mock external HTTP calls so they don't require a real API key.

## Continuous Integration

A GitHub Actions workflow is included at `.github/workflows/ci.yml`. On pull requests to `main` it will:

- Install dependencies from `requirements.txt`
- Run `flake8` (linting)
- Run `pytest`

If any tests require real secrets in CI, add `OPENWEATHER_API_KEY` as a repository secret under Settings → Secrets & variables → Actions.

## Notes and next steps

- The app uses an in-memory TTL cache suitable for development or single-instance deployments. For multi-instance or production use, swap this for Redis-backed `Flask-Caching`.
- Consider running the app under Gunicorn for production and adding a `/health` endpoint for healthchecks.
- The `WeatherClient` currently lives in `app.py` for simplicity — moving it to its own module improves testability and separation of concerns.

## Screenshots

![Screenshot](/images/screenshot1.png)

![Screenshot](/images/screenshot3.png)

![Screenshot](/images/screenshot6.png)

![Screenshot](/images/screenshot5.png)