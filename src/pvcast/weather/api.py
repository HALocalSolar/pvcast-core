"""WeatherAPI interface."""

from __future__ import annotations

import datetime as dt
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import pandas as pd
import voluptuous as vol
from pvlib.location import Location

from .const import DT_FORMAT, WEATHER_SCHEMA

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
        self.output_schema = {
            "cloud_cover": "dimensionless",
            "temperature": "celsius",
            "humidity": "dimensionless",
            "wind_speed": "m/s",
        }

    @abstractmethod
    def retrieve_new_data(self) -> pd.DataFrame:
        """Retrieve new weather data from the API.

        :return: Response from the API
        """

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, str]:
        """The input schema should specify the expected units for each of the
        response parameters. This is used to validate the response from the API
        and to convert to a common unit system.
        """

    def get_weather(self) -> pd.DataFrame:
        """Retrieve new weather data from the API.

        :return: Response from the API
        """
        _LOGGER.debug("Retrieving new weather data from %s", self.__class__)
        df = self.retrieve_new_data()

        # convert units to common unit system
        for key, value in self.output_schema.items():
            df[key] = df[key].pint.to(value)

        _LOGGER.debug("Weather data retrieved: \n%s", df.head(5))

        # validate the response
        self._validate(df.copy())

    def _validate(self, df: pd.DataFrame) -> None:
        """Validate the response from the API.

        :param df: Response from the API
        :return: Validated response
        """
        # convert to float
        for key in self.output_schema:
            df[key] = df[key].astype(float)

        # convert dt to string
        df["datetime"] = df["datetime"].dt.strftime(DT_FORMAT)

        data_list = df.to_dict("records")

        try:
            validated_data: dict[str, Any] = {
                "source": "test",
                "interval": "test",
                "data": data_list,
            }
            WEATHER_SCHEMA(validated_data)
        except vol.Invalid as exc:
            msg = f"Error validating weather data: {validated_data}"
            raise ValueError(msg) from exc


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

    def get_weather_api(self, api_id: str, **kwargs: Any) -> WeatherAPI:
        """Get a weather API instance.

        :param api_id: The identifier string of the API used in config.yaml.
        :param **kwargs: Passed to the weather API class.
        :return: The weather API instance.
        """
        try:
            weather_api_class: Callable[..., WeatherAPI] = self._apis[api_id]
        except KeyError as exc:
            msg = f"Unknown weather API: {api_id}"
            raise ValueError(msg) from exc

        return weather_api_class(**kwargs)

    def get_weather_api_list_obj(self) -> list[Callable[..., WeatherAPI]]:
        """Get a list of all registered weather API instances.

        :return: List of weather API classes.
        """
        return list(self._apis.values())

    def get_weather_api_list_str(self) -> list[str]:
        """Get a list of all registered weather API identifiers.

        :return: List of weather API identifiers.
        """
        return list(self._apis.keys())
