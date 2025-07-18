"""Configuration file for pytest containing customizations and fixtures.

In VSCode, Code Coverage is recorded in config.xml. Delete this file to reset reporting.

See https://stackoverflow.com/questions/34466027/in-pytest-what-is-the-use-of-conftest-py-files
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd
import pytest
import voluptuous as vol
from pvlib.location import Location
from src.pvcast.weather.api import API_FACTORY, WeatherAPI

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

    def retrieve_new_data(self) -> pd.DataFrame:
        """Retrieve new data from the API."""
        return pd.DataFrame()

    @property
    def input_schema(self) -> dict[str, str]:
        return {
            "cloud_cover": "pint[dimensionless]",
            "temperature": "pint[celsius]",
            "humidity": "pint[dimensionless]",
            "wind_speed": "pint[m/s]",
        }


SCHEMA = vol.Schema({vol.Required("type"): "mockweatherapi", vol.Required("name"): str})

API_FACTORY.register("mockweatherapi", MockWeatherAPI, SCHEMA)


@pytest.fixture(params=LOCATIONS)
def location(request: pytest.FixtureRequest) -> Location:
    """Fixture that creates a location."""
    return Location(*request.param)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Set up env variable."""
    os.environ["PVCAST_CONFIG"] = "tests/configs/test_config_string.yaml"


@pytest.fixture
def weather_df() -> pd.DataFrame:
    """Fixture for a basic pvlib input weather dataframe."""
    path = "tests/data/weather.csv"
    df = pd.read_csv(path, parse_dates=["time"])
    df["time"] = pd.to_datetime(df["time"])
    df["time"] = df["time"].dt.tz_convert("UTC")
    return df
