"""PV plant model."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from pvlib.modelchain import ModelChain
from pvlib.pvsystem import Array, FixedMount, PVSystem, retrieve_sam
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

from .const import RENAME_WEATHER_COLUMNS

if TYPE_CHECKING:
    from pvlib.location import Location

_LOGGER = logging.getLogger(__name__)


class Plant(ABC):
    """Implements the PV model chain based on the parameters set in config.yaml.

    This class is basically a wrapper around pvlib. Each entry under plant:
    list in config.yaml file should be instantiated as a PVModelChain object.
    In case of a PV system with microinverters, each microinverter is
    represented by one PVModelChain object.

    :param config: The PV plant configuration dictionary.
    :param loc: The location of the PV plant.
    """

    def __init__(self, *, simple: bool = False) -> None:
        """Class constructor."""
        self._plants: list[ModelChain] = []
        self._config: dict
        self._temp_param: dict[str, Any]
        self._location: Location
        self._modules: dict = {}
        self._inverters: dict = {}
        self._simple: bool = simple
        self._name = self._config["name"]
        self._results: pd.DataFrame | None = None

        _LOGGER.debug(
            "Creating PV system model of type %s, with config: %s",
            self.__class__.__name__,
            self._config,
        )

        # set temperature model
        self._temp_param = TEMPERATURE_MODEL_PARAMETERS["pvsyst"]["freestanding"]
        if self._simple:
            _LOGGER.debug("Using simple model for PV plant.")
            self._simple = True

        # construct plant model from config
        if not self._simple:
            self._collect_params()

        self._construct()
        _LOGGER.debug(
            "Created %d model chains for %s",
            len(self._plants),
            self._name,
        )

    @property
    def location(self) -> Location:
        """Return the location of the plant."""
        return self._location

    @property
    def results(self) -> pd.DataFrame:
        """Return the results of the plant model."""
        if self._results is None:
            msg = "Plant results are not available. Run the model first."
            raise ValueError(msg)

        # return a copy to avoid accidental modifications
        return self._results.copy()

    @abstractmethod
    def _construct(self) -> None:
        """Construct the PV plant model."""

    def _collect_params(self):
        """Collect all parameter dicts for the plant model."""
        module_params = retrieve_sam("CECMod")
        inverter_params = retrieve_sam("CECInverter")

        # first, module parameters
        try:
            for array in self._config["arrays"]:
                self._modules[array["module"]] = module_params[array["module"]]
        except KeyError as exc:
            msg = f"Invalid module in configuration: {exc}"
            raise KeyError(msg) from exc

        # then, inverter parameters
        try:
            if "inverter" in self._config:
                self._inverters[self._config["inverter"]] = inverter_params[
                    self._config["inverter"]
                ]
            for array in self._config["arrays"]:
                if "inverter" in array:
                    self._inverters[array["inverter"]] = inverter_params[
                        array["inverter"]
                    ]
        except KeyError as exc:
            msg = f"Invalid inverter in configuration: {exc}"
            raise KeyError(msg) from exc

    def run(self, weather_df: pd.DataFrame, *, add_individual: bool = False) -> None:
        """Run the model chain for each array in the plant.

        :param weather_df: The weather/irradiance dataframe to use for the
            simulation. Must contain a 'timestamp' column with timezone-aware
            datetime data.
        :param add_individual: If True, add individual plant AC power columns to the results.
        :raises ValueError: If required columns are missing or timestamp format
            is invalid.
        """
        result_df = weather_df.copy()
        weather_df = self._prepare_weather_data(weather_df)
        self._validate_weather_dataframe(weather_df)
        ac_power_results: list[pd.Series] = []
        total_ac_power = np.zeros(len(weather_df), dtype=float)

        # run model for each plant
        for plant in self._plants:
            try:
                plant.run_model(weather_df)
                ac = plant.results.ac

                if ac is not None:
                    # accumulate total AC power
                    ac_values = ac.to_numpy().flatten()
                    total_ac_power += ac_values

                    # store individual plant results with proper naming
                    ac_series = pd.Series(
                        ac_values, index=result_df.index, name=f"ac_{plant.name}"
                    )
                    ac_power_results.append(ac_series)
                    _LOGGER.debug(
                        "Model chain %s produced %.2f kW peak AC power",
                        plant.name,
                        ac_values.max() / 1000,
                    )
                else:
                    _LOGGER.warning(
                        "Model chain %s did not produce AC results. Skipping.",
                        plant.name,
                    )
            except RuntimeError:
                _LOGGER.exception(
                    "Error running model chain %s",
                    plant.name,
                )
                continue

        # add total AC power to result DataFrame
        result_df["ac"] = total_ac_power

        # add individual plant AC power columns
        if add_individual:
            for ac_series in ac_power_results:
                result_df[ac_series.name] = ac_series

        # store the results in the plant object
        self._results = result_df

        _LOGGER.info(
            "Completed simulation for %d model chains. Peak total AC power: %.2f kW",
            len(self._plants),
            total_ac_power.max() / 1000,
        )

    def _validate_weather_dataframe(self, weather_df: pd.DataFrame) -> None:
        """Validate the input weather DataFrame.

        :param weather_df: The weather DataFrame to validate.
        :raises ValueError: If validation fails.
        """
        if weather_df.empty:
            msg = "Weather DataFrame cannot be empty"
            raise ValueError(msg)

        # check that index is a DatetimeIndex
        if not isinstance(weather_df.index, pd.DatetimeIndex):
            msg = "Weather DataFrame index must be a pd.DatetimeIndex"
            raise TypeError(msg)

        # check for required weather columns (basic validation)
        required_cols = ["ghi", "dni", "dhi", "temp_air", "wind_speed"]
        missing_cols = [col for col in required_cols if col not in weather_df.columns]
        if missing_cols:
            _LOGGER.warning(
                "Missing optional weather columns: %s. "
                "Using default values where needed.",
                missing_cols,
            )

    def _prepare_weather_data(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """Prepare weather data for pvlib model chains.

        :param weather_df: The input weather DataFrame.
        :return: The prepared DataFrame with proper indexing for pvlib.
        """
        return weather_df.rename(columns=RENAME_WEATHER_COLUMNS)


class MicroPlant(Plant):
    """Micro inverter based PV plant model."""

    def __init__(
        self, config: dict, location: Location, *, simple: bool = False
    ) -> None:
        """Initialize the micro-inverter based PV plant model.

        :param config: The PV plant configuration dictionary.
        :param location: The physical location of the PV plant.
        """
        self._config = config
        self._location = location
        super().__init__(simple=simple)

    def _construct(self) -> None:
        """Construct the PV plant model.

        System uses microinverters, so we create a model chain for each array.
        """
        arrays = self._config["arrays"]

        # build model chains
        for array in arrays:
            modules_per_string = 1
            nr_inverters = 1
            mount = FixedMount(
                surface_tilt=array["tilt"],
                surface_azimuth=array["azimuth"],
            )

            # only dc/ac power is specified, so we use a simple model
            if self._simple:
                module_parameters = {"pdc0": array["dc_power"], "gamma_pdc": -0.004}
                inverter_parameters = {
                    "pdc0": array["ac_power"],
                    "eta_inv_nom": 0.96,
                }
            # full specification of module and inverter type numbers available
            else:
                module_parameters = self._modules[array["module"]]
                inverter_parameters = self._inverters[array["inverter"]]
                modules_per_string = array["modules_per_string"]
                nr_inverters = array["nr_inverters"]

            # micro inverter system, so each array is a separate model chain
            for i in range(nr_inverters):
                system = PVSystem(
                    arrays=[
                        Array(
                            mount=mount,
                            module_parameters=module_parameters,
                            temperature_model_parameters=self._temp_param,
                            strings=1,
                            modules_per_string=modules_per_string,
                        )
                    ],
                    inverter_parameters=inverter_parameters,
                    name=f"{self._name}_{array['name']}_{i}",
                )

                # create the model chain
                self._plants.append(
                    ModelChain(
                        system,
                        self._location,
                        aoi_model="physical",
                        name=f"{self._name}_{array['name']}_{i}",
                    )
                )


class StringPlant(Plant):
    """String inverter based PV plant model."""

    def __init__(
        self, config: dict, location: Location, *, simple: bool = False
    ) -> None:
        """Initialize the string inverter based PV plant model.

        :param config: The PV plant configuration dictionary.
        :param location: The physical location of the PV plant.
        """
        self._config = config
        self._location = location
        super().__init__(simple=simple)

    def _construct(self) -> None:
        """Construct the PV plant model.

        System uses a string inverter, so we create one model chain object.
        """
        arrays = []

        # get the inverter parameters
        inverter_parameters = {}
        if self._simple:
            inverter_parameters = {
                "pdc0": self._config["ac_power"],
                "eta_inv_nom": 0.96,
            }
        else:
            inverter_parameters = self._inverters[self._config["inverter"]]

        for array in self._config["arrays"]:
            module_parameters = {}
            strings = 1
            modules_per_string = 1

            # only dc/ac power is specified, so we use a simple model
            if self._simple:
                module_parameters = {
                    "pdc0": array["dc_power"],
                    "gamma_pdc": -0.004,
                }
            # full specification of module and inverter type numbers available
            else:
                module_parameters = self._modules[array["module"]]
                strings = array["strings"]
                modules_per_string = array["modules_per_string"]

            mount = FixedMount(
                surface_tilt=array["tilt"],
                surface_azimuth=array["azimuth"],
            )

            arrays.append(
                Array(
                    mount=mount,
                    module_parameters=module_parameters,
                    temperature_model_parameters=self._temp_param,
                    strings=strings,
                    modules_per_string=modules_per_string,
                )
            )

        # the PV system is constructed from the arrays and inverter parameters
        system = PVSystem(
            arrays=arrays,
            inverter_parameters=inverter_parameters,
            name=self._name,
        )
        self._plants = [
            ModelChain(system, self._location, aoi_model="physical", name=self._name)
        ]
