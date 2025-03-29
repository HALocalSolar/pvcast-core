"""Test the configreader module."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pytz import UnknownTimeZoneError
from src.pvcast.config.configreader import ConfigReader
from voluptuous import MultipleInvalid

from tests.const import TEST_CONF_ERR, TEST_CONF_STRING_PATH


class TestConfigReader:
    """Test the configreader module."""

    @pytest.fixture
    def configreader(self) -> ConfigReader:
        """Fixture for the configreader initialized without a secrets file and
        no !secret tags in config.
        """
        return ConfigReader(TEST_CONF_STRING_PATH)

    def test_configreader_no_secrets(self, configreader: ConfigReader) -> None:
        """Test the configreader without a secrets file and no !secret tags in config."""
        assert isinstance(configreader, ConfigReader)
        config = configreader.config
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
            _ = ConfigReader(config_file_path=TEST_CONF_ERR)

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Test that malformed YAML raises an error."""
        malformed_yaml = tmp_path / "bad.yaml"
        malformed_yaml.write_text("general:\n  location: [unclosed", encoding="utf-8")

        with pytest.raises(yaml.YAMLError):
            ConfigReader(config_file_path=malformed_yaml)

    def test_missing_required_fields(self, tmp_path: Path) -> None:
        """Test that missing required fields raise a schema validation error."""
        bad_schema = tmp_path / "missing.yaml"
        bad_schema.write_text("general: {}\nplant: []", encoding="utf-8")

        with pytest.raises(MultipleInvalid):
            ConfigReader(config_file_path=bad_schema)

    def test_correct_coercion_of_types(self, configreader: ConfigReader) -> None:
        """Test that coercion of float/bool types works as expected."""
        plant = configreader.config["plant"][0]
        assert isinstance(plant["microinverter"], bool)
        assert isinstance(plant["arrays"][0]["tilt"], float)
