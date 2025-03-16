"""Test the configreader module."""

from __future__ import annotations

from pathlib import Path

import pytest
from pytz import UnknownTimeZoneError

from src.pvcast.config.configreader import ConfigReader
from tests.const import (
    TEST_CONF_PATH_ERROR,
    TEST_CONF_PATH_NO_SEC,
    TEST_CONF_PATH_SEC,
    TEST_SECRETS_PATH,
)


class TestConfigReader:
    """Test the configreader module."""

    @pytest.fixture
    def configreader(self) -> ConfigReader:
        """Fixture for the configreader initialized without a secrets file and
        no !secret tags in config."""
        return ConfigReader(TEST_CONF_PATH_NO_SEC)

    def test_configreader_no_secrets(self, configreader: ConfigReader) -> None:
        """Test the configreader without a secrets file and no !secret tags in
        config."""
        assert isinstance(configreader, ConfigReader)
        config = configreader.config
        if not isinstance(config, dict):
            msg = "Config must be a dictionary."
            raise TypeError(msg)
        plant_config = config.get("plant")
        if not isinstance(plant_config, list):
            msg = "Plant config must be a list."
            raise TypeError(msg)
        assert config["plant"][0]["name"] == "EastWest"
        assert config["plant"][1]["name"] == "NorthSouth"

    def test_configreader_no_config_file(self) -> None:
        """Test the configreader without a config file."""
        with pytest.raises(TypeError):
            ConfigReader()  # type: ignore[call-arg]

    def test_configreader_wrong_config_file(self) -> None:
        """Test the configreader with a wrong config file."""
        with pytest.raises(FileNotFoundError):
            ConfigReader(Path("wrongfile.yaml"))

    def test_invalid_timezone(self) -> None:
        """Test the configreader with an invalid timezone."""
        with pytest.raises(UnknownTimeZoneError):
            _ = ConfigReader(config_file_path=TEST_CONF_PATH_ERROR)
