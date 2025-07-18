"""Reads PV plant configuration from a YAML file."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pytz
import voluptuous as vol
import yaml
from pytz import UnknownTimeZoneError

from src.pvcast.weather.api import API_FACTORY

from .schemas import PLANT_SCHEMA

_LOGGER = logging.getLogger(__name__)


def valid_timezone(value: str) -> str:
    """Validate that the input is a valid timezone string."""
    try:
        pytz.timezone(value)
    except UnknownTimeZoneError as exc:
        msg = f"Unknown timezone: {value}"
        raise vol.Invalid(msg) from exc
    else:
        return value


@dataclass
class ConfigReader:
    """Reads PV plant configuration from a YAML file."""

    _config: dict[str, vol.Any] = field(init=False, repr=False)
    config_file: Path | dict = field(init=True, repr=True)

    def __post_init__(self) -> None:
        """Initialize the class."""
        if isinstance(self.config_file, Path):
            if not self.config_file.exists():
                msg = f"Configuration file {self.config_file} not found."
                raise FileNotFoundError(msg)

            with self.config_file.open(encoding="utf-8") as config_file:
                try:
                    # load the main configuration file and validate
                    config = yaml.safe_load(config_file)
                except yaml.YAMLError as exc:
                    msg = (
                        f"Error parsing config.yaml with message: {exc}.\n"
                        "Please check the file for syntax errors."
                    )
                    _LOGGER.exception(msg)
                    raise yaml.YAMLError(msg) from exc
        elif isinstance(self.config_file, dict):
            # if config is a dict, we assume it is already parsed
            config = self.config_file
        else:
            msg = (
                f"Configuration file {self.config_file} is not a valid path "
                "or dictionary."
            )
            raise TypeError(msg)

        # validate the configuration file
        self._config = self._config_schema(config)

    @property
    def config(self) -> dict[str, vol.Any]:
        """Parse the YAML configuration and return it as a dictionary.

        :return: The configuration as a dictionary.
        """
        return self._config

    @property
    def _config_schema(self) -> vol.Schema:
        """Get the configuration schema as a Schema object.

        :return: Config schema.
        """
        weather_api_schemas = API_FACTORY.get_schema_list()

        # create the schema for the configuration file
        return vol.Schema(
            {
                vol.Required("general"): {
                    vol.Required("weather"): {
                        vol.Required("sources"): [
                            vol.Any(*weather_api_schemas),
                        ],
                    },
                    vol.Required("location"): {
                        vol.Required("latitude"): float,
                        vol.Required("longitude"): float,
                        vol.Required("altitude"): vol.Coerce(float),
                        vol.Required("timezone"): valid_timezone,
                    },
                },
                vol.Required("plant"): [PLANT_SCHEMA],
            }
        )
