"""Configuration file for pytest containing customizations and fixtures.

In VSCode, Code Coverage is recorded in config.xml. Delete this file to reset reporting.

See https://stackoverflow.com/questions/34466027/in-pytest-what-is-the-use-of-conftest-py-files
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest
from pvlib.location import Location

from src.pvcast.weather.api import WeatherAPI

LOCATIONS = [
    (52.3585, 4.8810, "Europe/Amsterdam", 0.0),
    (40.7211, -74.0701, "America/New_York", 10.0),
    (-31.9741, 115.8517, "Australia/Perth", 0.0),
]


class MockWeatherAPI(WeatherAPI):
    """Mock the WeatherAPI class."""

    def __init__(self, location: Location, **kwargs: Any) -> None:
        """Initialize the mock class."""
        super().__init__(location, **kwargs)

    def get_weather(self) -> pd.DataFrame:
        """Retrieve new data from the API."""
        return pd.DataFrame()


@pytest.fixture(params=LOCATIONS)
def location(request: pytest.FixtureRequest) -> Location:
    """Fixture that creates a location."""
    return Location(*request.param)
