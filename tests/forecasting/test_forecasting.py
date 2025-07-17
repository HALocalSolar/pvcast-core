"""Test forecasting functions."""

from __future__ import annotations

import pandas as pd
import pytest

from src.pvcast.forecasting.forecasting import add_precipitable_water


class TestForecasting:
    """Test forecasting functions."""

    def test_add_precipitable_water(self, weather_df: pd.DataFrame) -> None:
        """Test the add precipitable water method."""
        assert "precipitable_water" not in weather_df.columns
        weather_df = add_precipitable_water(weather_df)
        assert "precipitable_water" in weather_df.columns
        assert weather_df["precipitable_water"].dtype == "float64"
        assert weather_df["precipitable_water"].notnull().all()
        assert weather_df["precipitable_water"].notna().all()

    def test_add_precipitable_water_no_temp(
        self, weather_df: pd.DataFrame
    ) -> None:
        """Test the add precipitable water method with no temperature."""
        weather_df = weather_df.drop(columns=["temperature"])
        with pytest.raises(
            KeyError, match="Temperature missing from weather dataframe"
        ):
            add_precipitable_water(weather_df)

    def test_add_precipitable_water_no_humidity(
        self, weather_df: pd.DataFrame
    ) -> None:
        """Test the add precipitable water method with no humidity."""
        weather_df = weather_df.drop(columns=["humidity"])
        with pytest.raises(
            KeyError, match="Humidity missing from weather dataframe"
        ):
            add_precipitable_water(weather_df)
