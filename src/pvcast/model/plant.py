"""PV plant model."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.pvsystem import Array, FixedMount, PVSystem

from src.pvcast.config.const import MICRO_SYS, STRING_SYS

if TYPE_CHECKING:
    from types import MappingProxyType

_LOGGER = logging.getLogger(__name__)


class Plant(ABC):
    """Implements the PV model chain based on the parameters set in
    config.yaml.

    This class is basically a wrapper around pvlib. Each entry under plant:
    list in config.yaml file should be instantiated as a PVModelChain object.
    In case of a PV system with microinverters, each microinverter is
    represented by one PVModelChain object.

    :param config: The PV plant configuration dictionary.
    :param loc: The location of the PV plant.
    """

    def __init__(self) -> None:
        """Class constructor."""
        _LOGGER.debug(
            "Creating PV system model of type %s", self.__class__.__name__
        )

    @abstractmethod
    def construct(self, config: MappingProxyType[str, Any]) -> None:
        """Construct the PV plant model."""


class MicroPlant(Plant):
    """
    Micro inverter based PV plant model.
    """

    def __init__(self, config: dict) -> None:
        try:
            self._config = MICRO_SYS(config)
        except vol.MultipleInvalid as exc:
            raise vol.Invalid(
                f"Invalid configuration for micro inverter: {exc}"
            ) from exc

    def construct(self, config: MappingProxyType[str, Any]) -> None:
        """Construct the PV plant model."""


class StringPlant(Plant):
    """
    String inverter based PV plant model.
    """

    def __init__(self, config: dict) -> None:
        try:
            self._config = STRING_SYS(config)
        except vol.MultipleInvalid as exc:
            raise vol.Invalid(
                f"Invalid configuration for string inverter: {exc}"
            ) from exc

    def construct(self, config: MappingProxyType[str, Any]) -> None:
        """Construct the PV plant model."""
