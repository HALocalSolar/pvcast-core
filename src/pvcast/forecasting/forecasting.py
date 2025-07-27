"""Base forecasting functionality for pvcast."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import pandas as pd

from pvcast.weather.atmospheric import add_precipitable_water

if TYPE_CHECKING:
    from src.pvcast.model.manager import SystemManager


class ForecastType(Enum):
    """Enum for the type of PVPlantResults."""

    LIVE = "live"
    CLEARSKY = "clearsky"
    HISTORICAL = "historical"


@dataclass
class ForecastResult:
    """Object to store the aggregated results of the PV simulation.

    :param fc_type: The type of the result.
    :param ac_power: The sum of AC power outputs of all ModelChain objects
        in the PV plant.
    """

    fc_type: ForecastType
    ac_power: pd.DataFrame = field(repr=False, default=pd.DataFrame())


@dataclass
class PowerEstimate(ABC):
    """Abstract base class to do PV power estimation."""

    manager: SystemManager = field(repr=False)
    fc_type: ForecastType = field()
    _model_attrs: dict[str, str] = field(repr=False, default_factory=dict, init=False)

    def run(self, weather_df: pd.DataFrame) -> ForecastResult:
        """Run power estimate and store results.

        :param weather_df: The weather data or datetimes to forecast for.
        :return: A ForecastResult object containing the results of the power estimate.
        """
        weather_df = self._prepare_weather(weather_df)

        # run the forecast for each model chain
        result_df = pd.DataFrame()

    @abstractmethod
    def _prepare_weather(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare weather data for the forecast. This method should be implemented by subclasses.

        When calling this function it may be required to provide weather
        data or datetimes to forecast for. Datetimes must always be ordered and provided
        in a column named 'datetime'. Weather data must be provided in a DataFrame with
        the following columns: [datetime, cloud_cover, wind_speed, temperature, humidity,
        dni, dhi, ghi]. Other columns are ignored.
        """


@dataclass
class Live(PowerEstimate):
    """Class for PV power forecasts based on live weather data."""

    fc_type: ForecastType = ForecastType.LIVE

    def _prepare_weather(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        return add_precipitable_water(weather_df)


@dataclass
class Clearsky(PowerEstimate):
    """Class for PV power forecasts based on weather data."""

    fc_type: ForecastType = ForecastType.CLEARSKY

    def _prepare_weather(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        pass
