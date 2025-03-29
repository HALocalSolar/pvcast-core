"""Constants for the Weather component of PVCast."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import voluptuous as vol

DT_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _validate_sorted_and_evenly_spaced(data: list) -> list:
    """Validate that the timestamps are sorted and evenly spaced."""
    timestamps = [entry["datetime"] for entry in data]

    # check for gaps
    dt_diffs = np.diff(timestamps)
    if not all(dt_diffs == dt_diffs[0]):
        raise vol.Invalid("Gaps in data detected. Data must be evenly spaced.")
    return data


# schema for weather data
WEATHER_SCHEMA = vol.Schema(
    vol.All(
        [
            {
                vol.Required("datetime"): vol.All(datetime),
                vol.Required("temperature"): vol.All(
                    vol.Coerce(float), vol.Range(min=-100, max=100)
                ),
                vol.Required("humidity"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=100)
                ),
                vol.Required("wind_speed"): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("wind_direction"): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Required("cloud_cover"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=100)
                ),
                vol.Optional("ghi"): vol.All(vol.Coerce(float), vol.Range(0, 1400)),
                vol.Optional("dni"): vol.All(vol.Coerce(float), vol.Range(0, 1400)),
                vol.Optional("dhi"): vol.All(vol.Coerce(float), vol.Range(0, 1400)),
            }
        ],
        vol.Length(min=1),
        _validate_sorted_and_evenly_spaced,
    ),
)
