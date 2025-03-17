"""Test the configreader module."""

from __future__ import annotations

from pathlib import Path

import pytest
import regex as re
import voluptuous as vol
import yaml
from pytz import UnknownTimeZoneError

from src.pvcast.config.configreader import ConfigReader
from tests.const import (
    TEST_CONF_ERR,
    TEST_CONF_MALFORMED,
    TEST_CONF_MISSING,
    TEST_CONF_STRING_PATH,
)


class TestConfigReader:
    """Test the configreader module."""

    @pytest.fixture
    def configreader(self) -> ConfigReader:
        """Fixture for the configreader initialized without a secrets file and
        no !secret tags in config."""
        return ConfigReader(TEST_CONF_STRING_PATH)

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
            ConfigReader()

    def test_configreader_wrong_entry(self) -> None:
        """Test the configreader with a wrong config file."""
        with pytest.raises(FileNotFoundError):
            ConfigReader(Path("wrongfile.yaml"))

    def test_configreader_missing(self) -> None:
        """Test the configreader with missing fields in the config file."""
        # required key not provided @ data['general']['location']
        with pytest.raises(
            vol.error.MultipleInvalid,
            match=re.escape(
                "required key not provided @ data['general']['location']"
            ),
        ):
            ConfigReader(TEST_CONF_MISSING)

    def test_invalid_timezone(self) -> None:
        """Test the configreader with an invalid timezone."""
        with pytest.raises(UnknownTimeZoneError):
            _ = ConfigReader(config_file_path=TEST_CONF_ERR)

    def test_configreader_yaml_error(self, tmp_path: Path) -> None:
        """Test the configreader with a malformed YAML file to trigger
        yaml.YAMLError."""
        malformed_yaml = tmp_path / "malformed_config.yaml"
        malformed_yaml.write_text(
            "general:\n  location:\n    timezone: [Invalid YAML"
        )

        with pytest.raises(
            yaml.YAMLError,
            match="Error parsing config.yaml file with message:",
        ):
            ConfigReader(TEST_CONF_MALFORMED)
