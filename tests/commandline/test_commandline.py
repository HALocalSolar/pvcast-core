"""Commandline interface for pvcast unit tests."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from src.pvcast.commandline.commandline import _check_file_exists, get_args


class TestCommandline:
    """Test the commandline module."""

    def test_check_file_exists_existing_file(self, tmp_path: Path) -> None:
        """Test if _check_file_exists returns the file path if the file exists."""
        file_path = tmp_path / "existing_file.txt"
        file_path.touch()
        result = _check_file_exists(file_path)
        assert result == file_path

    def test_check_file_exists_non_existing_file(self, tmp_path: Path) -> None:
        """Test _check_file_exists raises an error if file does not exist."""
        non_existing_file = tmp_path / "non_existing_file.txt"
        with pytest.raises(argparse.ArgumentTypeError, match="does not exist"):
            _check_file_exists(non_existing_file)

    def test_check_file_exists_directory(self, tmp_path: Path) -> None:
        """Test _check_file_exists raises an error if the path is a dir."""
        directory = tmp_path / "directory"
        directory.mkdir()
        with pytest.raises(argparse.ArgumentTypeError, match="is not a file"):
            _check_file_exists(directory)

    def test_check_file_exists_not_path(self) -> None:
        """Test _check_file_exists raises error if path is not a Path obj."""
        with pytest.raises(
            argparse.ArgumentTypeError, match="is not a valid path"
        ):
            _check_file_exists("not_a_path")  # type: ignore[arg-type]

    @patch("argparse.ArgumentParser.parse_args")
    @patch("src.pvcast.commandline.commandline._check_file_exists")
    def test_get_args(
        self,
        mock_check_file_exists: MagicMock,
        mock_parse_args: MagicMock,  # Add this argument
    ) -> None:
        """Test if get_args returns the correct arguments."""
        # mocking the _check_file_exists function
        mock_parse_args.return_value = argparse.Namespace(
            config="test_config.yaml",
            log_level="DEBUG",
            workers=5,
        )
        mock_check_file_exists.side_effect = lambda x: Path(x)

        args = get_args()

        # assertions
        assert args["log_level"] == logging.DEBUG
        assert args["config"] == "test_config.yaml"
        assert args["workers"] == 5

        # ensure _check_file_exists is called with the correct arguments
        calls = [call("test_config.yaml")]
        mock_check_file_exists.assert_has_calls(calls, any_order=True)

    @patch("src.pvcast.commandline.commandline._check_file_exists")
    def test_get_args_defaults(
        self, mock_check_file_exists: MagicMock
    ) -> None:
        """Test get_args returns correct defaults if no CLI args are passed."""
        with patch.object(sys, "argv", ["prog"]):  # Simulate no arguments
            # Mock _check_file_exists to return the path without error
            mock_check_file_exists.side_effect = (
                lambda x: x
            )  # Identity function

            args = get_args()

            # Assert default values
            assert args["log_level"] == logging.INFO
            assert args["config"] == Path("config.yaml")
            assert args["host"] == "127.0.0.1"
            assert args["port"] == 4557

            # Check that CONFIG_FILE_PATH was set
            assert os.environ["CONFIG_FILE_PATH"] == str(Path("config.yaml"))

            # Ensure _check_file_exists was called with the default config path
            mock_check_file_exists.assert_called_once_with(Path("config.yaml"))
