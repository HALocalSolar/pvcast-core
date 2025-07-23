"""Test the system manager module."""

from __future__ import annotations

import os

import pytest
from pvlib.location import Location
from src.pvcast.model.manager import SYSTEM, SystemManager


class TestSystemManager:
    """Test the weather factory module."""

    @pytest.fixture
    def sys(self) -> SystemManager:
        """Create a SystemManager instance."""
        # set the environment variable for testing
        return SystemManager()

    def test_init(self, sys: SystemManager) -> None:
        """Test the SystemManager initialization."""
        assert sys is not None
        assert isinstance(sys.location, Location)
        assert sys.location.latitude == 52.35845515630293
        assert sys.location.longitude == 4.88115070391368
        assert sys.location.altitude == 0.0
        assert sys.location.tz == "UTC"

    def test_init_env_var_not_set(self) -> None:
        """Test initialization when PVCAST_CONFIG environment var not set."""
        # remove the environment variable for testing
        os.environ.pop("PVCAST_CONFIG", None)
        with pytest.raises(
            OSError, match="PVCAST_CONFIG environment variable not set."
        ):
            SystemManager()

    def test_init_config_file_not_found(self) -> None:
        """Test initialization when config file not found."""
        os.environ["PVCAST_CONFIG"] = "non_existent_file.yaml"
        with pytest.raises(
            FileNotFoundError,
            match="Config file non_existent_file.yaml not found.",
        ):
            SystemManager()

    def test_init_config_file_is_directory(self) -> None:
        """Test initialization when config file is a directory."""
        os.environ["PVCAST_CONFIG"] = "."
        with pytest.raises(
            IsADirectoryError,
            match="Config file . is a directory.",
        ):
            SystemManager()

    def test_manager_global_instance(self) -> None:
        """Test the global instance of SystemManager."""
        assert SYSTEM is not None
        assert isinstance(SYSTEM, SystemManager)

    def test_get_pv_plants(self, sys: SystemManager) -> None:
        """Test getting PV plants from the SystemManager."""
        pv_plants = sys.pv_plants
        assert isinstance(pv_plants, dict)
        assert len(pv_plants) > 0
        for name, plant in pv_plants.items():
            assert isinstance(name, str)
            assert name in [p["name"] for p in sys.config["plant"]]
            assert isinstance(plant, plant.__class__)
