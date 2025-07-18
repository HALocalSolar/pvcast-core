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

        _LOGGER.debug("Weather data retrieved: \n%s", df.head(24))

        validated_data: list = self._validate(df.copy())
        return pd.DataFrame.from_records(validated_data)

    def _validate(self, df: pd.DataFrame) -> list:
        """Validate the response from the API.

        :param df: Response from the API
        :return: Validated response
        """
        # convert to float
        for key in self.output_schema:
            df[key] = df[key].astype(float)

        data_list = df.to_dict("records")
        try:
            validated_data = WEATHER_SCHEMA(data_list)
        except vol.Invalid as exc:
            msg = f"Error validating weather data: {data_list} message: {exc}"
            raise ValueError(msg) from exc

        return validated_data


class WeatherAPIFactory:
    """Factory class for weather APIs."""

    def __init__(self) -> None:
        self._apis: dict[str, Callable[..., WeatherAPI]] = {}
        self._schemas: dict[str, vol.Schema] = {}

    def register(
        self,
        api_id: str,
        weather_api_class: Callable[..., WeatherAPI],
        schema: vol.Schema,
    ) -> None:
        """Register a new weather API class to the factory.

        :param api_id: The identifier string of the API used in config.yaml.
        :param weather_api_class: The weather API class.
        """
        self._apis[api_id] = weather_api_class
        self._schemas[api_id] = schema
        _LOGGER.debug("Registered weather API: %s", api_id)

    def get_weather_api(self, api_id: str, **kwargs: Any) -> WeatherAPI:
        """Get a weather API instance.

        :param api_id: The identifier string of the API used in config.yaml.
        :param **kwargs: Passed to the weather API class.
        :return: The weather API instance.
        """
        print(f"current apis: {self._apis}")
        try:
            weather_api_class: Callable[..., WeatherAPI] = self._apis[api_id]
        except KeyError as exc:
            msg = f"Unknown weather API: {api_id}"
            raise ValueError(msg) from exc

        return weather_api_class(**kwargs)

    def get_weather_api_schema(self, api_id: str) -> vol.Schema:
        """Get the schema for a weather API.

        :param api_id: The identifier string of the API used in config.yaml.
        :return: The schema for the weather API.
        """
        try:
            return self._schemas[api_id]
        except KeyError as exc:
            msg = f"Unknown weather API schema: {api_id}"
            raise ValueError(msg) from exc

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

    def get_schema_list(self) -> list[vol.Schema]:
        """Get a list of all registered weather API schemas.

        :return: List of weather API schemas.
        """
        return list(self._schemas.values())


API_FACTORY = WeatherAPIFactory()
