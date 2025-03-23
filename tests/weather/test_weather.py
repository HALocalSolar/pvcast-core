"""Test the weather module."""

from __future__ import annotations

import pandas as pd
import pytest
from pvlib.location import Location

from src.pvcast.weather.api import WeatherAPI, WeatherAPIFactory

from ..conftest import MockWeatherAPI


class CommonWeatherTests:
    """Test common weather API functionality.

    These tests can be run on both the abstract WeatherAPI class and on
    platforms that inherit from it. This class should no run platform specific
    tests.
    """

    @pytest.mark.parametrize("weather_api", [], indirect=True)
    def test_weather_init(self, weather_api: WeatherAPI):
        """Test the WeatherAPI initialization."""
        assert weather_api is not None


class WeatherProviderTests:
    """Test the weather provider API functionality."""

    def test_get_weather(self, weather_api: WeatherAPI) -> None:
        """Test the get_weather function."""
        df = weather_api.get_weather()
        # weather = pd.DataFrame.from_dict(data)
        # assert isinstance(weather, pd.DataFrame)
        # # assert weather.null_count().sum_horizontal().item() == 0
        # assert weather.shape[0] >= 24


class TestWeatherFactory:
    """Test the weather factory module."""

    test_url = "http://fakeurl.com/status/"

    @pytest.fixture
    def weather_api_factory(self) -> WeatherAPIFactory:
        """Get a weather API factory."""
        api_factory_test = WeatherAPIFactory()
        api_factory_test.register("mock", MockWeatherAPI)
        return api_factory_test

    def test_get_weather_api(
        self,
        weather_api_factory: WeatherAPIFactory,
    ) -> None:
        """Test the get_weather_api function."""
        assert isinstance(weather_api_factory, WeatherAPIFactory)
        assert isinstance(
            weather_api_factory.get_weather_api(
                "mock",
                location=Location(0, 0, "UTC", 0),
            ),
            MockWeatherAPI,
        )
        with pytest.raises(ValueError, match="Unknown weather API"):
            weather_api_factory.get_weather_api(
                "wrong_api", location=Location(0, 0, "UTC", 0)
            )

    def test_get_weather_api_list_obj(
        self, weather_api_factory: WeatherAPIFactory
    ) -> None:
        """Test the get_weather_api function with a list of objects."""
        assert isinstance(weather_api_factory, WeatherAPIFactory)
        api_list = weather_api_factory.get_weather_api_list_obj()
        assert isinstance(api_list, list)
        assert len(api_list) == 1

    def test_get_weather_api_list_str(
        self, weather_api_factory: WeatherAPIFactory
    ) -> None:
        """Test the get_weather_api function with a list of strings."""
        assert isinstance(weather_api_factory, WeatherAPIFactory)
        api_list = weather_api_factory.get_weather_api_list_str()
        assert isinstance(api_list, list)
        assert len(api_list) == 1
        assert api_list[0] == "mock"
