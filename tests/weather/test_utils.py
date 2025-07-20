"""Test suite for atmospheric weather utilities in pvcast."""

import pandas as pd
import pytest
from pvlib.location import Location
from src.pvcast.weather.atmospheric import cloud_cover_to_irradiance


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
