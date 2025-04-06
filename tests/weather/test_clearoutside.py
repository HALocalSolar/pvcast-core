"""Test all configured weather platforms that inherit from WeatherAPI class."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin

import pytest
import responses
from pvlib.location import Location
from src.pvcast.weather import API_FACTORY
from src.pvcast.weather.api import WeatherAPI

from .test_weather import WeatherProviderTests


class TestClearOutsideWeather(WeatherProviderTests):
    """Clearoutside specific weather API setup and tests."""

    @pytest.fixture(scope="session")
    def clearoutside_html_page(self) -> str:
        """Load the clearoutside html page."""
        with Path.open(
            Path("tests/data/clearoutside.txt"), encoding="utf-8"
        ) as html_file:
            return html_file.read()

    @pytest.fixture
    def clearoutside_api(
        self, location: Location, clearoutside_html_page: str
    ) -> Generator[WeatherAPI]:
        """Set up the Clear Outside API."""
        lat = str(round(location.latitude, 2))
        lon = str(round(location.longitude, 2))

        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                urljoin("https://clearoutside.com/forecast/", f"{lat}/{lon}"),
                body=clearoutside_html_page,
                status=200,
            )
            api = API_FACTORY.get_weather_api("clearoutside", location=location)
            yield api

    @pytest.fixture
    def weather_api(self, clearoutside_api: WeatherAPI) -> WeatherAPI:
        """Return the weather api."""
        return clearoutside_api
