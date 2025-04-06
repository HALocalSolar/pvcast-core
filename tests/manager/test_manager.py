"""Test the system manager module."""

from __future__ import annotations

import os

import pytest
from src.pvcast.model.manager import SystemManager, system


class TestSystemManager:
    """Test the weather factory module."""

    @pytest.fixture
    def system_manager(self) -> SystemManager:
        """Create a SystemManager instance."""
        # set the environment variable for testing
        return SystemManager()

    def test_init(self, system_manager: SystemManager) -> None:
        """Test the SystemManager initialization."""
        assert system_manager is not None
        assert system_manager.config is not None
        assert isinstance(system_manager.config, dict)

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
        assert system is not None
