"""Reads PV plant configuration from a YAML file."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytz
import yaml
from pytz import UnknownTimeZoneError
from voluptuous import Any, Coerce, Required, Schema

from src.pvcast.weather.api import API_FACTORY

from .const import PLANT_SCHEMAS

if TYPE_CHECKING:
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)


@dataclass
class ConfigReader:
    """Reads PV plant configuration from a YAML file."""

    _config: dict[str, Any] = field(init=False, repr=False)
    config_file_path: Path = field(repr=True)

    def __post_init__(self) -> None:
        """Initialize the class."""
        if not self.config_file_path.exists():
            msg = f"Configuration file {self.config_file_path} not found."
            raise FileNotFoundError(msg)

        with self.config_file_path.open(encoding="utf-8") as config_file:
            try:
                # load the main configuration file
                config = yaml.safe_load(config_file)

                # validate the configuration
                print(self._config_schema)
                config = Schema(self._config_schema)(config)
            except yaml.YAMLError as exc:
                msg = (
                    f"Error parsing config.yaml file with message: {exc}.\n"
                    "Please check the file for syntax errors."
                )
                _LOGGER.exception(msg)
                raise yaml.YAMLError(msg) from exc

        # check if the timezone is valid
        try:
            config["general"]["location"]["timezone"] = pytz.timezone(
                config["general"]["location"]["timezone"]
            )
        except UnknownTimeZoneError as exc:
            msg = f"Unknown timezone {config['general']['location']['timezone']}"
            raise UnknownTimeZoneError(msg) from exc

        self._config = config

    @property
    def config(self) -> dict[str, Any]:
        """Parse the YAML configuration and return it as a dictionary.

        :return: The configuration as a dictionary.
        """
        return self._config

    @property
    def _config_schema(self) -> Schema:
        """Get the configuration schema as a Schema object.

        :return: Config schema.
        """
        weather_api_schemas = API_FACTORY.get_schema_list()
        plant_schemas = PLANT_SCHEMAS

        # create the schema for the configuration file
        return Schema(
            {
                Required("general"): {
                    Required("weather"): {
                        Required("sources"): [
                            Any(
                                *weather_api_schemas,
                            ),
                        ],
                    },
                    Required("location"): {
                        Required("latitude"): float,
                        Required("longitude"): float,
                        Required("altitude"): Coerce(float),
                        Required("timezone"): str,
                    },
                },
                Required("plant"): [Any(*plant_schemas)],
            }
        )
