"""Test PV plant creation."""

from __future__ import annotations

import pandas as pd
import pytest
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from src.pvcast.model.plant import MicroPlant, StringPlant
from src.pvcast.weather.atmospheric import (
    add_precipitable_water,
    cloud_cover_to_irradiance,
)

from tests.const import (
    CONFIG_MICRO_DICT,
    CONFIG_SIMPLE_MICRO_DICT,
    CONFIG_SIMPLE_STRING_DICT,
    CONFIG_STRING_DICT,
    LOCATIONS,
    Loc,
)


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
        return MicroPlant(config["plant"][0], location)

    @pytest.mark.parametrize("location", LOCATIONS, indirect=True)
    @pytest.mark.parametrize("string_plant", [CONFIG_STRING_DICT], indirect=True)
    def test_init_string_plant(self, string_plant: StringPlant) -> None:
        """Test the string plant."""
        assert isinstance(string_plant, StringPlant)
        assert isinstance(string_plant._config, dict)
        assert isinstance(string_plant._location, Location)
        assert isinstance(string_plant._plants, list)
        assert all(isinstance(plant, ModelChain) for plant in string_plant._plants)
        assert isinstance(string_plant._temp_param, dict)
        assert len(string_plant._plants) == 1
        assert string_plant._simple is False

    @pytest.mark.parametrize("location", LOCATIONS, indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_init_micro_plant(self, micro_plant: MicroPlant) -> None:
        """Test the micro plant."""
        assert isinstance(micro_plant, MicroPlant)
        assert isinstance(micro_plant._config, dict)
        assert isinstance(micro_plant._location, Location)
        assert isinstance(micro_plant._plants, list)
        assert all(isinstance(plant, ModelChain) for plant in micro_plant._plants)
        assert isinstance(micro_plant._temp_param, dict)
        assert len(micro_plant._plants) == sum(
            array["nr_inverters"] for array in micro_plant._config["arrays"]
        )
        assert micro_plant._simple is False

    @pytest.mark.parametrize("location", LOCATIONS, indirect=True)
    @pytest.mark.parametrize("string_plant", [CONFIG_SIMPLE_STRING_DICT], indirect=True)
    def test_init_simple_string_plant(self, string_plant: StringPlant) -> None:
        """Test the simple string plant."""
        assert isinstance(string_plant, StringPlant)
        assert isinstance(string_plant._config, dict)
        assert isinstance(string_plant._location, Location)
        assert isinstance(string_plant._plants, list)
        assert all(isinstance(plant, ModelChain) for plant in string_plant._plants)
        assert isinstance(string_plant._temp_param, dict)
        assert len(string_plant._plants) == 1
        assert string_plant._simple is True

    @pytest.mark.parametrize("location", LOCATIONS, indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_SIMPLE_MICRO_DICT], indirect=True)
    def test_init_micro_plant_simple(self, micro_plant: MicroPlant) -> None:
        """Test the simple micro plant."""
        assert isinstance(micro_plant, MicroPlant)
        assert isinstance(micro_plant._config, dict)
        assert isinstance(micro_plant._location, Location)
        assert isinstance(micro_plant._plants, list)
        assert all(isinstance(plant, ModelChain) for plant in micro_plant._plants)
        assert isinstance(micro_plant._temp_param, dict)
        assert len(micro_plant._plants) == len(micro_plant._config["arrays"])
        assert micro_plant._simple is True

    def test_init_pv_system_wrong_inverter(self) -> None:
        """Test the PV system with wrong inverter."""
        with pytest.raises(
            KeyError,
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
                            "modules_per_string": 1,
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
            KeyError,
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
                            "modules_per_string": 1,
                            "nr_inverters": 4,
                            "module": "wrong",
                            "inverter": "SolarEdge_Technologies_Ltd___SE4000__240V_",
                        }
                    ],
                },
                Location(0.0, 0.0),
            )

    @pytest.mark.parametrize("location", LOCATIONS, indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_run_forecast_micro(
        self, micro_plant: MicroPlant, weather_df: pd.DataFrame
    ) -> None:
        """Test the run method of the micro plant."""
        assert isinstance(micro_plant, MicroPlant)
        assert callable(micro_plant.run)
        assert isinstance(weather_df, pd.DataFrame)

        # add irradiance data
        weather_df = cloud_cover_to_irradiance(
            weather_df,
            how="clearsky_scaling",
            location=micro_plant.location,
            merge=True,
        )

        # add precipitable water
        weather_df = add_precipitable_water(weather_df)
        micro_plant.run(weather_df)

        # check results
        assert isinstance(micro_plant.results, pd.DataFrame)
        assert "ac" in micro_plant.results.columns
        assert len(micro_plant.results) == len(weather_df)

    @pytest.mark.parametrize("location", [LOCATIONS[0]], indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_empty_weather_df(self, micro_plant: MicroPlant) -> None:
        """Test the run method with an empty weather DataFrame."""
        empty_df = pd.DataFrame(columns=["timestamp", "cloud_cover"])
        with pytest.raises(ValueError, match="Weather DataFrame cannot be empty"):
            micro_plant.run(empty_df)

    @pytest.mark.parametrize("location", [LOCATIONS[0]], indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_results_not_available(self, micro_plant: MicroPlant) -> None:
        """Test results when model has not been run."""
        with pytest.raises(
            ValueError, match="Plant results are not available. Run the model first."
        ):
            _ = micro_plant.results

    @pytest.mark.parametrize("location", LOCATIONS, indirect=True)
    @pytest.mark.parametrize("string_plant", [CONFIG_STRING_DICT], indirect=True)
    def test_run_forecast_string(
        self, string_plant: StringPlant, weather_df: pd.DataFrame
    ) -> None:
        """Test the run method of the string plant."""
        assert isinstance(string_plant, StringPlant)
        assert callable(string_plant.run)
        assert isinstance(weather_df, pd.DataFrame)

        # add irradiance data
        weather_df = cloud_cover_to_irradiance(
            weather_df,
            how="clearsky_scaling",
            location=string_plant.location,
            merge=True,
        )

        # add precipitable water
        weather_df = add_precipitable_water(weather_df)

        # run forecast
        string_plant.run(weather_df)

        # check results
        assert isinstance(string_plant.results, pd.DataFrame)
        assert "ac" in string_plant.results.columns
        assert len(string_plant.results) == len(weather_df)

    @pytest.mark.parametrize("location", [LOCATIONS[0]], indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_run_with_add_individual(
        self, micro_plant: MicroPlant, weather_df: pd.DataFrame
    ) -> None:
        """Test the run method with add_individual=True."""
        # add irradiance data
        weather_df = cloud_cover_to_irradiance(
            weather_df,
            how="clearsky_scaling",
            location=micro_plant.location,
            merge=True,
        )

        # add precipitable water
        weather_df = add_precipitable_water(weather_df)

        # run forecast with add_individual=True
        micro_plant.run(weather_df, add_individual=True)

        # check results
        assert isinstance(micro_plant.results, pd.DataFrame)
        assert "ac" in micro_plant.results.columns

        # check that individual plant columns are added
        individual_columns = [
            col for col in micro_plant.results.columns if col.startswith("ac_")
        ]
        assert len(individual_columns) > 0

        # verify we have the expected number of individual plants
        expected_plants = sum(
            array["nr_inverters"] for array in micro_plant._config["arrays"]
        )
        assert len(individual_columns) == expected_plants

    @pytest.mark.parametrize("location", [LOCATIONS[0]], indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_invalid_weather_index_type(
        self, micro_plant: MicroPlant, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test the run method with invalid weather DataFrame index type."""
        weather_df = pd.DataFrame(
            {
                "ghi": [500, 600],
                "dni": [700, 800],
                "dhi": [200, 300],
                "temp_air": [20, 25],
                "wind_speed": [2, 3],
            }
        )

        # return a DataFrame with a regular index (not DatetimeIndex)
        def mock_prepare_weather_data(self, weather_df):  # noqa: ANN001, ANN202
            prepared_df = weather_df.copy()
            prepared_df.index = pd.Index(["invalid", "index"])
            return prepared_df

        monkeypatch.setattr(
            "src.pvcast.model.plant.Plant._prepare_weather_data",
            mock_prepare_weather_data,
        )

        # this should raise TypeError when validating the index type
        with pytest.raises(
            TypeError, match="Weather DataFrame index must be a pd.DatetimeIndex"
        ):
            micro_plant.run(weather_df)

    @pytest.mark.parametrize("location", [LOCATIONS[0]], indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_runtime_error_handling(
        self,
        micro_plant: MicroPlant,
        weather_df: pd.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that RuntimeError in model chain run is handled gracefully."""
        # add irradiance data
        weather_df = cloud_cover_to_irradiance(
            weather_df,
            how="clearsky_scaling",
            location=micro_plant.location,
            merge=True,
        )

        # add precipitable water
        weather_df = add_precipitable_water(weather_df)

        # mock run_model to raise RuntimeError for all plants
        def mock_run_model_error(self, weather_data):  # noqa: ANN001, ANN202
            msg = "Simulated model chain error"
            raise RuntimeError(msg)

        # apply the monkeypatch to ModelChain.run_model
        monkeypatch.setattr(
            "pvlib.modelchain.ModelChain.run_model", mock_run_model_error
        )

        # this should not raise an exception, but should log errors and continue
        micro_plant.run(weather_df)

        # should have results DataFrame with zero AC power
        assert isinstance(micro_plant.results, pd.DataFrame)
        assert "ac" in micro_plant.results.columns
        assert (micro_plant.results["ac"] == 0).all()

    @pytest.mark.parametrize("location", [LOCATIONS[0]], indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_none_ac_results_handling(
        self,
        micro_plant: MicroPlant,
        weather_df: pd.DataFrame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that None AC results are handled gracefully."""
        weather_df = cloud_cover_to_irradiance(
            weather_df,
            how="clearsky_scaling",
            location=micro_plant.location,
            merge=True,
        )
        weather_df = add_precipitable_water(weather_df)

        # mock run_model to set ac results to None
        def mock_run_model_none_ac(self, _weather_data):  # noqa: ANN001, ANN202
            class MockResults:
                ac = None

            self.results = MockResults()

        # apply the monkeypatch to ModelChain.run_model
        monkeypatch.setattr(
            "pvlib.modelchain.ModelChain.run_model", mock_run_model_none_ac
        )

        # this should not raise an exception, but should log warnings and continue
        micro_plant.run(weather_df)

        # check results - should have results DataFrame with zero AC power
        assert isinstance(micro_plant.results, pd.DataFrame)
        assert "ac" in micro_plant.results.columns
        assert (micro_plant.results["ac"] == 0).all()

    @pytest.mark.parametrize("location", [LOCATIONS[0]], indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_missing_weather_columns_warning(
        self,
        micro_plant: MicroPlant,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that missing optional weather columns log a warning."""
        import logging

        # create weather DataFrame with minimum required columns for pvlib
        # but missing some "optional" columns that our validation checks for
        weather_df = pd.DataFrame(
            {
                "ghi": [500, 600, 700],
                "dni": [700, 800, 900],
                "dhi": [200, 250, 300],  # required by pvlib
                # missing "temp_air", "wind_speed" - these are "optional"
            },
            index=pd.DatetimeIndex(
                [
                    "2025-03-23 13:00:00+00:00",
                    "2025-03-23 14:00:00+00:00",
                    "2025-03-23 15:00:00+00:00",
                ]
            ),
        )

        # set log level to capture warnings
        with caplog.at_level(logging.WARNING):
            # run the model - this should trigger the missing columns warning
            micro_plant.run(weather_df)

        # check that warning was logged about missing columns
        assert len(caplog.records) > 0
        warning_messages = [
            record.message
            for record in caplog.records
            if record.levelno == logging.WARNING
        ]
        assert any(
            "Missing optional weather columns" in msg for msg in warning_messages
        )

        # verify the specific missing columns are mentioned
        missing_columns_warning = next(
            (
                msg
                for msg in warning_messages
                if "Missing optional weather columns" in msg
            ),
            None,
        )
        assert missing_columns_warning is not None
        assert "temp_air" in missing_columns_warning
        assert "wind_speed" in missing_columns_warning

        # verify that present columns are not mentioned as missing
        assert "ghi" not in missing_columns_warning
        assert "dni" not in missing_columns_warning
        assert "dhi" not in missing_columns_warning

    @pytest.mark.parametrize("location", [LOCATIONS[0]], indirect=True)
    @pytest.mark.parametrize("micro_plant", [CONFIG_MICRO_DICT], indirect=True)
    def test_complete_weather_columns_no_warning(
        self,
        micro_plant: MicroPlant,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that no warning is logged when all required columns are present."""
        import logging

        # create weather DataFrame with all required columns
        weather_df = pd.DataFrame(
            {
                "ghi": [500, 600, 700],
                "dni": [700, 800, 900],
                "dhi": [200, 250, 300],
                "temp_air": [20, 22, 25],
                "wind_speed": [2.5, 3.0, 3.5],
            },
            index=pd.DatetimeIndex(
                [
                    "2025-03-23 13:00:00+00:00",
                    "2025-03-23 14:00:00+00:00",
                    "2025-03-23 15:00:00+00:00",
                ]
            ),
        )

        # set log level to capture warnings
        with caplog.at_level(logging.WARNING):
            # run the model - this should NOT trigger missing columns warning
            micro_plant.run(weather_df)

        # check that no warning about missing columns was logged
        warning_messages = [
            record.message
            for record in caplog.records
            if record.levelno == logging.WARNING
        ]
        assert not any(
            "Missing optional weather columns" in msg for msg in warning_messages
        )
