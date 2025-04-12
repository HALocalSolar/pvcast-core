"""Test PV plant creation."""

from __future__ import annotations

import pytest
import voluptuous as vol
from pvlib.location import Location
from pvlib.modelchain import ModelChain

from src.pvcast.model.plant import MicroPlant, StringPlant
from tests.const import CONFIG_MICRO_DICT, CONFIG_STRING_DICT, LOCATIONS, Loc


class TestPlant:
    """Test PV plant creation."""

    @pytest.fixture
    def location(self, request: pytest.FixtureRequest) -> Location:
        """Fixture for location."""
        loc: Loc = request.param
        return Location(
            latitude=loc.latitude,
            longitude=loc.longitude,
            tz="UTC",
            altitude=loc.altitude,
        )

    @pytest.fixture
    def string_plant(
        self, request: pytest.FixtureRequest, location: Location
    ) -> StringPlant:
        """Fixture for the string plant."""
        config: dict = request.param
        return StringPlant(config["plant"][0], location)

    @pytest.fixture
    def micro_plant(
        self, request: pytest.FixtureRequest, location: Location
    ) -> MicroPlant:
        """Fixture for the micro plant."""
        config: dict = request.param
        plant = MicroPlant(config["plant"][0], location)
        print("Recreating micro plant")
        return plant

    @pytest.mark.parametrize("location", LOCATIONS, indirect=True)
    @pytest.mark.parametrize(
        "string_plant", [CONFIG_STRING_DICT], indirect=True
    )
    def test_init_string_plant(self, string_plant: StringPlant) -> None:
        """Test the string plant."""
        assert isinstance(string_plant, StringPlant)
        assert isinstance(string_plant._config, dict)
        assert isinstance(string_plant._schema, vol.Schema)
        assert isinstance(string_plant._location, Location)
        assert isinstance(string_plant._plants, list)
        assert all(
            isinstance(plant, ModelChain) for plant in string_plant._plants
        )
        assert isinstance(string_plant._temp_param, dict)
        assert len(string_plant._plants) == 1

    @pytest.mark.parametrize("location", LOCATIONS, indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_init_micro_plant(self, micro_plant: MicroPlant) -> None:
        """Test the micro plant."""
        assert isinstance(micro_plant, MicroPlant)
        assert isinstance(micro_plant._config, dict)
        assert isinstance(micro_plant._schema, vol.Schema)
        assert isinstance(micro_plant._location, Location)
        assert isinstance(micro_plant._plants, list)
        assert all(
            isinstance(plant, ModelChain) for plant in micro_plant._plants
        )
        assert isinstance(micro_plant._temp_param, dict)
        assert len(micro_plant._plants) == sum(
            array["nr_inverters"] for array in micro_plant._config["arrays"]
        )

    def test_init_pv_system_wrong_inverter(self) -> None:
        """Test the PV system with wrong inverter."""
        with pytest.raises(
            vol.Invalid,
            match="Invalid inverter in configuration: 'wrong'",
        ):
            MicroPlant(
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
                            "inverter": "wrong",
                        }
                    ],
                },
                Location(0.0, 0.0),
            )

    def test_init_pv_system_wrong_module(self) -> None:
        """Test the PV system with wrong module."""
        with pytest.raises(
            vol.Invalid,
            match="Invalid module in configuration: 'wrong'",
        ):
            MicroPlant(
                {
                    "name": "EastWest",
                    "arrays": [
                        {
                            "name": "East",
                            "tilt": 30,
                            "azimuth": 90,
                            "modules_per_inverter": 1,
                            "nr_inverters": 4,
                            "module": "wrong",
                            "inverter": "SolarEdge_Technologies_Ltd___SE4000__240V_",
                        }
                    ],
                },
                Location(0.0, 0.0),
            )
