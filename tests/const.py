"""Constants for all tests."""

from __future__ import annotations

# location named tuple import
from collections import namedtuple
from pathlib import Path

Loc = namedtuple(
    "Location",
    ["latitude", "longitude", "timezone", "altitude"],
)
LOC_EUW = Loc(
    52.3585,
    4.8810,
    "Europe/Amsterdam",
    0.0,
)
LOC_USW = Loc(
    40.7211,
    -74.0701,
    "America/New_York",
    10.0,
)
LOC_AUS = Loc(
    -31.9741,
    115.8517,
    "Australia/Perth",
    0.0,
)

LOCATIONS = [LOC_EUW, LOC_USW, LOC_AUS]

TEST_CONF_STRING_PATH = Path(__file__).parent / "configs" / "test_config_string.yaml"
TEST_CONF_ERR = Path(__file__).parent / "configs" / "test_config_error.yaml"
TEST_CONF_MICRO_PATH = Path(__file__).parent / "configs" / "test_config_micro.yaml"
TEST_CONF_MISSING = (
    Path(__file__).parent / "configs" / "test_config_missing_sources.yaml"
)

HASS_TEST_URL = "192.168.1.217:8123"
HASS_TEST_TOKEN = """eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhMTI1Mzg4MTVlZDk0M\
zRmODQ0YjJmMGIzZDc1MGVmOSIsImlhdCI6MTcwMTQ0MjQwNywiZXhwIjoyMDE2ODAyNDA3fQ.KkHCfCuFdkUyP\
b3LNA8HcEvIH2IQ1rmtSDn3haGbKeM"""  # noqa: S105
HASS_WEATHER_ENTITY_ID = "weather.forecast_thuis"

# this must be one of the keys in the config file due to
# get_weather_sources in file pvcast/webserver/models/live.py
MOCK_WEATHER_API = "ClearOutside"

CONFIG_STRING_DICT = {
    "general": {
        "weather": {"sources": [{"name": "CO", "type": "mockweatherapi"}]},
        "location": {
            "latitude": 52.35845515630293,
            "longitude": 4.88115070391368,
            "altitude": 0.0,
            "timezone": "Europe/Amsterdam",
        },
    },
    "plant": [
        {
            "name": "EastWest",
            "inverter": "SolarEdge_Technologies_Ltd___SE4000__240V_",
            "arrays": [
                {
                    "name": "East",
                    "tilt": 30.0,
                    "azimuth": 90.0,
                    "modules_per_string": 4,
                    "strings": 1,
                    "module": "Trina_Solar_TSM_330DD14A_II_",
                },
                {
                    "name": "West",
                    "tilt": 30.0,
                    "azimuth": 270.0,
                    "modules_per_string": 8,
                    "strings": 1,
                    "module": "Trina_Solar_TSM_330DD14A_II_",
                },
            ],
        },
        {
            "name": "NorthSouth",
            "inverter": "SolarEdge_Technologies_Ltd___SE4000__240V_",
            "arrays": [
                {
                    "name": "North",
                    "tilt": 30.0,
                    "azimuth": 0.0,
                    "modules_per_string": 4,
                    "strings": 1,
                    "module": "Trina_Solar_TSM_330DD14A_II_",
                },
                {
                    "name": "South",
                    "tilt": 30.0,
                    "azimuth": 180.0,
                    "modules_per_string": 8,
                    "strings": 1,
                    "module": "Trina_Solar_TSM_330DD14A_II_",
                },
            ],
        },
    ],
}

CONFIG_MICRO_DICT = {
    "general": {
        "weather": {"sources": [{"name": "CO", "type": "mockweatherapi"}]},
        "location": {
            "latitude": 52.35845515630293,
            "longitude": 4.88115070391368,
            "altitude": 0,
            "timezone": "Europe/Amsterdam",
        },
    },
    "plant": [
        {
            "name": "EastWest",
            "arrays": [
                {
                    "name": "East",
                    "tilt": 30,
                    "azimuth": 90,
                    "modules_per_inverter": 1,
                    "nr_inverters": 4,
                    "module": "Trina_Solar_TSM_330DD14A_II_",
                    "inverter": "Enphase_Energy_Inc___IQ7X_96_x_ACM_US__240V_",
                },
                {
                    "name": "West",
                    "tilt": 10,
                    "azimuth": 270,
                    "modules_per_inverter": 1,
                    "nr_inverters": 4,
                    "module": "Trina_Solar_TSM_330DD14A_II_",
                    "inverter": "Enphase_Energy_Inc___IQ7X_96_x_ACM_US__240V_",
                },
            ],
        },
        {
            "name": "NorthSouth",
            "arrays": [
                {
                    "name": "North",
                    "tilt": 25,
                    "azimuth": 0,
                    "modules_per_inverter": 1,
                    "nr_inverters": 4,
                    "module": "Trina_Solar_TSM_330DD14A_II_",
                    "inverter": "Enphase_Energy_Inc___IQ7X_96_x_ACM_US__240V_",
                },
                {
                    "name": "West",
                    "tilt": 20,
                    "azimuth": 180,
                    "modules_per_inverter": 1,
                    "nr_inverters": 4,
                    "module": "Trina_Solar_TSM_330DD14A_II_",
                    "inverter": "Enphase_Energy_Inc___IQ7X_96_x_ACM_US__240V_",
                },
            ],
        },
    ],
}
