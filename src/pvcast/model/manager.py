"""PV system manager."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from pvlib.location import Location

from src.pvcast.config.configreader import ConfigReader

_LOGGER = logging.getLogger(__name__)


class SystemManager:
    """Interface between the PV system model and the rest of the application.

    This class is responsible for:
     - Instantiating the PV system model from a configuration file
     - Running live weather-based, clearsky and historical data simulations
     - Returning properly formatted results. All timeseries are in UTC.
    """

    def __init__(self) -> None:
        """Class constructor."""
        config_path = os.getenv("PVCAST_CONFIG")
        if config_path is None:
            raise OSError("PVCAST_CONFIG environment variable not set.")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file {config_path} not found.")
        if not os.path.isfile(config_path):
            raise IsADirectoryError(f"Config file {config_path} is a directory.")

        # read the configuration file
        config_file = ConfigReader(Path(config_path))
        _LOGGER.debug("System initialized with config: \n%s", config_file)

        # get the location from the config
        loc = config_file.config["general"]["location"]
        self._loc = Location(
            latitude=loc["latitude"],
            longitude=loc["longitude"],
            tz="UTC",
            altitude=loc["altitude"],
            name=f"PV system {loc['latitude']}, {loc['longitude']}",
        )

    @property
    def location(self) -> Location:
        """Return the location object."""
        return self._loc


# Global instance of the SystemManager
system = SystemManager()
