"""PV system manager."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from pvlib.location import Location
from voluptuous import Invalid

from src.pvcast.config.configreader import ConfigReader
from src.pvcast.config.schemas import (
    PLANT_SCHEMA,
    SYSTEM_FULL_MICRO,
    SYSTEM_FULL_STRING,
    SYSTEM_SIMPLE_MICRO,
    SYSTEM_SIMPLE_STRING,
)
from src.pvcast.forecasting.forecasting import (
    Clearsky,
    Live,
)
from src.pvcast.model.plant import MicroPlant, Plant, StringPlant

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
            msg = "PVCAST_CONFIG environment variable not set."
            raise OSError(msg)
        if not Path(config_path).exists():
            msg = f"Config file {config_path} not found."
            raise FileNotFoundError(msg)
        if not Path(config_path).is_file():
            msg = f"Config file {config_path} is a directory."
            raise IsADirectoryError(msg)

        config_file: ConfigReader = ConfigReader(Path(config_path))
        _LOGGER.debug("System initialized with config: \n%s", config_file)

        # get the location from the config
        self._config: dict[str, Any] = config_file.config
        loc = self._config["general"]["location"]
        self._location = Location(
            latitude=loc["latitude"],
            longitude=loc["longitude"],
            tz="UTC",
            altitude=loc["altitude"],
            name=f"PV system {loc['latitude']}, {loc['longitude']}",
        )

        # plants
        self._pv_plants: dict[str, Plant] = self._create_plants()

        # forecast results
        self._clearsky = Clearsky(manager=self)
        self._live = Live(manager=self)

    @property
    def config(self) -> dict[str, Any]:
        """Return the configuration dictionary."""
        return self._config

    @property
    def location(self) -> Location:
        """Return the location object."""
        return self._location

    @property
    def pv_plants(self) -> dict[str, Plant]:
        """The PV plants."""
        return self._pv_plants

    @property
    def clearsky(self) -> Clearsky:
        """The clear sky forecast result."""
        return self._clearsky

    @property
    def live(self) -> Live:
        """The live weather-based forecast result."""
        return self._live

    def get_pv_plant(self, name: str) -> Plant:
        """Get a PV plant model by name.

        :param name: The name of the PV plant.
        :return: The PV plant model.
        """
        try:
            return self._pv_plants[name]
        except KeyError as exc:
            msg = f"PV plant {name} not found."
            raise KeyError(msg) from exc

    def _create_plants(self) -> dict[str, Plant]:
        """Create PV plants from the configuration.

        :return: A dictionary of PV plants.
        """
        plants: dict[str, Plant] = {}
        for raw_config in self.config["plant"]:
            # Validate and normalize the configuration
            validated_config = PLANT_SCHEMA(raw_config)
            plant = self._create_single_plant(validated_config)
            plants[validated_config["name"]] = plant
        return plants

    def _create_single_plant(self, config: dict[str, Any]) -> Plant:
        """Create a single PV plant from validated configuration.

        :param config: Validated plant configuration.
        :return: The created plant instance.
        """
        # list of (schema, plant_class, is_simple) tuples to try in order
        plant_options = [
            (SYSTEM_SIMPLE_MICRO, MicroPlant, True),
            (SYSTEM_SIMPLE_STRING, StringPlant, True),
            (SYSTEM_FULL_MICRO, MicroPlant, False),
            (SYSTEM_FULL_STRING, StringPlant, False),
        ]

        # find the matching schema by re-validating
        for schema, plant_class, is_simple in plant_options:
            try:
                schema(config)
                return plant_class(config, self._location, simple=is_simple)
            except Invalid:
                continue

        # this should never happen due to PLANT_SCHEMA validation
        msg = f"Unable to determine plant type for config: {config}"
        _LOGGER.error(msg)
        raise ValueError(msg)


# Global instance of the SystemManager
SYSTEM = SystemManager()
