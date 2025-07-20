"""Test suite for atmospheric weather utilities in pvcast."""

import pandas as pd
import pytest
from pvlib.location import Location
from src.pvcast.weather.atmospheric import (
    add_precipitable_water,
    cloud_cover_to_irradiance,
)


class TestAtmospheric:
    """Test suite for atmospheric weather utilities."""

    @pytest.mark.parametrize("how", ["clearsky_scaling", "campbell_norman"])
    def test_cloud_cover_to_irradiance(
        self,
        how: str,
        weather_df: pd.DataFrame,
        location: Location,
    ) -> None:
        """Test the cloud_cover_to_irradiance function."""
        assert isinstance(weather_df, pd.DataFrame)
        assert weather_df["cloud_cover"].dtype == float
        irrads = cloud_cover_to_irradiance(weather_df, how=how, location=location)
        assert isinstance(irrads, pd.DataFrame)
        for irr in ["ghi", "dni", "dhi"]:
            assert irr in irrads.columns
            assert irrads[irr].dtype == float
            assert irrads[irr].min() >= 0
            assert irrads[irr].max() <= 1370
            assert len(irrads[irr]) == len(weather_df)
            assert irrads[irr].isna().sum() == 0

    def test_invalid_how_argument(
        self, weather_df: pd.DataFrame, location: Location
    ) -> None:
        """Test cloud_cover_to_irradiance with an invalid 'how' argument."""
        with pytest.raises(ValueError, match="Invalid how argument: invalid_method"):
            cloud_cover_to_irradiance(
                weather_df, how="invalid_method", location=location
            )

    def test_missing_timestamp_column(self) -> None:
        """Test cloud_cover_to_irradiance with missing 'timestamp' column."""
        weather_data = pd.DataFrame(
            {
                "cloud_cover": [0.1, 0.2, 0.3],
                "temperature": [20, 21, 22],
            }
        )
        with pytest.raises(
            ValueError, match="cloud_cover DataFrame must contain a 'timestamp' column."
        ):
            cloud_cover_to_irradiance(
                weather_data, how="clearsky_scaling", location=Location(0, 0)
            )

    def test_empty_dataframe(self, location: Location) -> None:
        """Test cloud_cover_to_irradiance with an empty DataFrame."""
        empty_df = pd.DataFrame(columns=["timestamp", "cloud_cover"])
        irrads = cloud_cover_to_irradiance(
            empty_df, how="clearsky_scaling", location=location
        )
        assert isinstance(irrads, pd.DataFrame)
        assert irrads.empty

    def test_merge_option(self, weather_df: pd.DataFrame, location: Location) -> None:
        """Test cloud_cover_to_irradiance with merge option."""
        irrads = cloud_cover_to_irradiance(
            weather_df, how="clearsky_scaling", location=location, merge=True
        )
        assert set(weather_df.columns).issubset(set(irrads.columns))
        assert "ghi" in irrads.columns
        assert "dni" in irrads.columns
        assert "dhi" in irrads.columns
        assert len(irrads) == len(weather_df)
        assert not irrads["timestamp"].isna().any()
        assert not irrads["cloud_cover"].isna().any()

    def test_add_precipitable_water(self, weather_df: pd.DataFrame) -> None:
        """Test the add precipitable water method."""
        assert "precipitable_water" not in weather_df.columns
        weather_df = add_precipitable_water(weather_df)
        assert "precipitable_water" in weather_df.columns
        assert weather_df["precipitable_water"].dtype == "float64"
        assert weather_df["precipitable_water"].notnull().all()
        assert weather_df["precipitable_water"].notna().all()

    def test_add_precipitable_water_no_temp(self, weather_df: pd.DataFrame) -> None:
        """Test the add precipitable water method with no temperature."""
        weather_df = weather_df.drop(columns=["temperature"])
        with pytest.raises(
            KeyError, match="Temperature missing from weather dataframe"
        ):
            add_precipitable_water(weather_df)

    def test_add_precipitable_water_no_humidity(self, weather_df: pd.DataFrame) -> None:
        """Test the add precipitable water method with no humidity."""
        weather_df = weather_df.drop(columns=["humidity"])
        with pytest.raises(KeyError, match="Humidity missing from weather dataframe"):
            add_precipitable_water(weather_df)
