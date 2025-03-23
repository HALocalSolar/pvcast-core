"""WeatherAPI interface."""

from __future__ import annotations

import datetime as dt
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

import pandas as pd
from pvlib.location import Location

from .const import WEATHER_SCHEMA

_LOGGER = logging.getLogger(__name__)


class WeatherAPI(ABC):
    """Abstract WeatherAPI interface class."""

    def __init__(
        self,
        location: Location,
        timeout: dt.timedelta = dt.timedelta(seconds=10),
    ):
        """Class constructor."""
        self.timeout = timeout
        self.location = location

    @abstractmethod
    def get_weather(self) -> pd.DataFrame:
        """Retrieve new weather data from the API.

        :return: Response from the API
        """


class WeatherAPIFactory:
    """Factory class for weather APIs."""

    def __init__(self) -> None:
        self._apis: dict[str, Callable[..., WeatherAPI]] = {}

    def register(
        self, api_id: str, weather_api_class: Callable[..., WeatherAPI]
    ) -> None:
        """Register a new weather API class to the factory.

        :param api_id: The identifier string of the API used in config.yaml.
        :param weather_api_class: The weather API class.
        """
        self._apis[api_id] = weather_api_class

    def get_weather_api(self, api_id: str, **kwargs: Any) -> "WeatherAPI":
        """Get a weather API instance.

        :param api_id: The identifier string of the API used in config.yaml.
        :param **kwargs: Passed to the weather API class.
        :return: The weather API instance.
        """
        try:
            weather_api_class: Callable[..., "WeatherAPI"] = self._apis[api_id]
        except KeyError as exc:
            msg = f"Unknown weather API: {api_id}"
            raise ValueError(msg) from exc

        return weather_api_class(**kwargs)

    def get_weather_api_list_obj(self) -> list[Callable[..., "WeatherAPI"]]:
        """Get a list of all registered weather API instances.

        :return: List of weather API classes.
        """
        return list(self._apis.values())

    def get_weather_api_list_str(self) -> list[str]:
        """Get a list of all registered weather API identifiers.

        :return: List of weather API identifiers.
        """
        return list(self._apis.keys())
