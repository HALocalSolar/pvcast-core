"""PV plant model."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import pandas as pd
import voluptuous as vol
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.pvsystem import Array, FixedMount, PVSystem, retrieve_sam
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

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
        self._plants: list[ModelChain] = []
        self._config: dict
        self._schema: vol.Schema
        self._temp_param: MappingProxyType[str, Any]
        self._location: Location
        self._modules: dict = {}
        self._inverters: dict = {}

        _LOGGER.debug(
            "Creating PV system model of type %s, with config: %s",
            self.__class__.__name__,
            self._config,
        )
        try:
            self._config = self._schema(self._config)
        except vol.MultipleInvalid as exc:
            raise vol.Invalid(
                f"Invalid configuration for micro inverter: {exc}"
            ) from exc

        # set temperature model
        self._temp_param = TEMPERATURE_MODEL_PARAMETERS["pvsyst"]["freestanding"]

        # construct plant model from config
        self._collect_params()
        self._construct()

    @abstractmethod
    def _construct(self) -> None:
        """Construct the PV plant model."""

    def _collect_params(self):
        """Collect all parameter dicts for the plant model."""
        module_params = retrieve_sam("CECMod")
        inverter_params = retrieve_sam("CECInverter")

        # first, modules
        try:
            for array in self._config["arrays"]:
                self._modules[array["module"]] = module_params[array["module"]]
        except KeyError as exc:
            raise vol.Invalid(f"Invalid module in configuration: {exc}") from exc

        # then, inverters
        try:
            if "inverter" in self._config.keys():
                self._inverters[self._config["inverter"]] = inverter_params[
                    self._config["inverter"]
                ]
            else:
                for array in self._config["arrays"]:
                    self._inverters[array["inverter"]] = inverter_params[
                        array["inverter"]
                    ]
        except KeyError as exc:
            raise vol.Invalid(f"Invalid inverter in configuration: {exc}") from exc

    def run(self, weather_df: pd.DataFrame) -> None:
        """Run the model chain for each array in the plant.

        :param weather: The weather data to use for the simulation.
        """
        # for plant in self._plants:
        #     plant.run_model(weather)


class MicroPlant(Plant):
    """Micro inverter based PV plant model."""

    def __init__(self, config: dict, location: Location) -> None:
        self._config = config
        self._schema = MICRO_SYS
        self._location = location
        super().__init__()

    def _construct(self) -> None:
        """Construct the PV plant model.

        System uses microinverters, so we create a model chain for each array.
        """
        name = self._config["name"]
        arrays = self._config["arrays"]

        # build model chains
        for array in arrays:
            mount = FixedMount(
                surface_tilt=array["tilt"],
                surface_azimuth=array["azimuth"],
            )

            # obtain the module and inverter parameters
            module_parameters = self._modules[array["module"]]
            inverter_parameters = self._inverters[array["inverter"]]

            # micro inverter system, so each array is a separate model chain
            for i in range(array["nr_inverters"]):
                system = PVSystem(
                    arrays=[
                        Array(
                            mount=mount,
                            module_parameters=module_parameters,
                            temperature_model_parameters=self._temp_param,
                            strings=array["modules_per_inverter"],
                            modules_per_string=array["modules_per_inverter"],
                        )
                    ],
                    inverter_parameters=inverter_parameters,
                    name=f"{name}_{array['name']}_{i}",
                )

                # create the model chain
                self._plants.append(
                    ModelChain(system, self._location, aoi_model="physical")
                )
        _LOGGER.debug(
            "Created %d model chains for %s",
            len(self._plants),
            name,
        )


class StringPlant(Plant):
    """String inverter based PV plant model."""

    def __init__(self, config: dict, location: Location) -> None:
        self._config = config
        self._schema = STRING_SYS
        self._location = location
        super().__init__()

    def _construct(self) -> None:
        """Construct the PV plant model.

        System uses a string inverter, so we create one model chain object.
        """
        name = self._config["name"]
        inverter = self._config["inverter"]

        # build PV arrays from the configuration
        arrays = [
            Array(
                mount=FixedMount(
                    surface_tilt=array["tilt"],
                    surface_azimuth=array["azimuth"],
                ),
                module_parameters=self._modules[array["module"]],
                temperature_model_parameters=self._temp_param,
                strings=array["strings"],
                modules_per_string=array["modules_per_string"],
            )
            for array in self._config["arrays"]
        ]

        # create the PV system object
        system = PVSystem(
            arrays=arrays,
            inverter_parameters=self._inverters[inverter],
            name=name,
        )
        self._plants = [ModelChain(system, self._location, aoi_model="physical")]
