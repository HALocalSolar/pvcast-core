"""Base forecasting functionality for pvcast."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

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
    :param ac_power: The sum of AC power outputs of all ModelChain objects
        in the PV plant.
    """

    fc_type: ForecastType
    ac_power: pd.DataFrame | None = field(repr=False, default=None)
