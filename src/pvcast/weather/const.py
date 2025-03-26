"""Constants for the Weather component of PVCast."""

from __future__ import annotations

import voluptuous as vol

DT_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# schema for weather data
WEATHER_SCHEMA = vol.Schema(
    {
        vol.Required("source"): str,
        vol.Required("interval"): str,
        vol.Required("data"): [
            {
                vol.Required("datetime"): vol.All(
                    str, vol.Datetime(format=DT_FORMAT)
                ),  # RFC 3339
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
                vol.Optional("ghi"): vol.All(
                    vol.Coerce(float), vol.Range(0, 1400)
                ),
                vol.Optional("dni"): vol.All(
                    vol.Coerce(float), vol.Range(0, 1400)
                ),
                vol.Optional("dhi"): vol.All(
                    vol.Coerce(float), vol.Range(0, 1400)
                ),
            }
        ],
    }
)
