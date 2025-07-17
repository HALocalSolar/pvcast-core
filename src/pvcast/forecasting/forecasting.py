"""Base forecasting functionality for pvcast."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from pvlib.atmosphere import gueymard94_pw

if TYPE_CHECKING:
    import pandas as pd


class ForecastType(Enum):
    """Enum for the type of PVPlantResults."""

    LIVE = "live"
    CLEARSKY = "clearsky"
    HISTORICAL = "historical"


@dataclass
class ForecastResult:
    """Object to store the aggregated results of the PV simulation.

    :param fc_type: The type of the result.
    :param ac_power: The sum of AC power outputs of all ModelChain objects in the PV plant.
    """

    fc_type: ForecastType
    ac_power: pd.DataFrame | None = field(repr=False, default=None)


def add_precipitable_water(weather_df: pd.DataFrame) -> pd.DataFrame:
    """Add precipitable water to the weather dataframe."""
    if "temperature" not in weather_df:
        msg = "Temperature missing from weather dataframe"
        raise KeyError(msg)
    if "humidity" not in weather_df:
        msg = "Humidity missing from weather dataframe"
        raise KeyError(msg)
    temperature = weather_df["temperature"].to_numpy()
    humidity = weather_df["humidity"].to_numpy()
    precipitable_water = gueymard94_pw(temperature, humidity)
    weather_df["precipitable_water"] = precipitable_water
    return weather_df
