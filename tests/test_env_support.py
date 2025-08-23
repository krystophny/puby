"""Tests for .env file support and environment variable handling."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from puby.cli import cli
from puby.env import load_api_keys, get_api_key


class TestEnvSupport:
    """Test environment variable and .env file support."""

    def test_load_env_file_in_current_directory(self):
        """Test loading .env file from current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .env file with API key
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("ZOTERO_API_KEY=test_key_from_env\n")
            
            # Change to temp directory and load
            original_cwd = os.getcwd()
            # Clear any existing environment variable
            original_env = os.environ.pop("ZOTERO_API_KEY", None)
            try:
                os.chdir(tmpdir)
                env_vars = load_api_keys()
                assert env_vars.get("ZOTERO_API_KEY") == "test_key_from_env"
            finally:
                os.chdir(original_cwd)
                # Restore environment
                if original_env is not None:
                    os.environ["ZOTERO_API_KEY"] = original_env

    def test_load_env_file_in_home_directory(self):
        """Test loading .env file from home directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .env file with API key
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("ZOTERO_API_KEY=test_key_from_home\n")
            
            # Mock home directory and current directory with no .env
            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                with patch("pathlib.Path.cwd", return_value=Path(tmpdir + "_fake")):
                    with patch.dict(os.environ, {}, clear=True):
                        env_vars = load_api_keys()
                        assert env_vars.get("ZOTERO_API_KEY") == "test_key_from_home"

    def test_current_dir_env_takes_precedence_over_home(self):
        """Test that .env in current directory takes precedence over home."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.TemporaryDirectory() as homedir:
                # Create .env in both locations
                home_env = Path(homedir) / ".env"
                home_env.write_text("ZOTERO_API_KEY=home_key\n")
                
                current_env = Path(tmpdir) / ".env"
                current_env.write_text("ZOTERO_API_KEY=current_key\n")
                
                # Mock both directories and clear environment
                with patch("pathlib.Path.home", return_value=Path(homedir)):
                    with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                        with patch.dict(os.environ, {}, clear=True):
                            env_vars = load_api_keys()
                            # Current directory should take precedence
                            assert env_vars.get("ZOTERO_API_KEY") == "current_key"

    def test_env_variable_loaded_from_environment(self):
        """Test that environment variables are loaded."""
        with patch.dict(os.environ, {"ZOTERO_API_KEY": "env_var_key"}):
            env_vars = load_api_keys()
            assert env_vars.get("ZOTERO_API_KEY") == "env_var_key"

    def test_command_line_overrides_env_file(self):
        """Test that command line argument overrides .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .env file
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("ZOTERO_API_KEY=env_file_key\n")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Command line value should override .env
                api_key = get_api_key("cli_key")
                assert api_key == "cli_key"
            finally:
                os.chdir(original_cwd)

    def test_env_file_used_when_no_command_line(self):
        """Test that .env file is used when no command line argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .env file
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("ZOTERO_API_KEY=env_file_key\n")
            
            # Mock current directory and clear environment
            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {}, clear=True):
                    # No command line value, should use .env
                    api_key = get_api_key(None)
                    assert api_key == "env_file_key"

    def test_none_returned_when_no_api_key(self):
        """Test that None is returned when no API key available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # No .env file, no command line, no environment
                with patch.dict(os.environ, {}, clear=True):
                    api_key = get_api_key(None)
                    assert api_key is None
            finally:
                os.chdir(original_cwd)

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ZoteroLibrary")
    def test_cli_uses_env_file_for_zotero(self, mock_zotero, mock_client):
        """Test that CLI loads API key from .env file."""
        runner = CliRunner()
        
        # Clear existing environment variable
        original_env = os.environ.pop("ZOTERO_API_KEY", None)
        try:
            with runner.isolated_filesystem():
                # Create .env file
                Path(".env").write_text("ZOTERO_API_KEY=abcdef1234567890abcdef78\n")
                
                # Mock Zotero to check API key
                mock_zotero_instance = Mock()
                mock_zotero_instance.publications = []
                mock_zotero.return_value = mock_zotero_instance
                
                # Mock client
                mock_client_instance = Mock()
                mock_client.return_value = mock_client_instance
                mock_client_instance.fetch_publications.return_value = []
                
                # Run command without --api-key
                # The isolated filesystem should ensure we read the .env file we created
                result = runner.invoke(
                    cli,
                    [
                        "check",
                        "--orcid", "https://orcid.org/0000-0000-0000-0000",
                        "--zotero", "12345",
                    ],
                    catch_exceptions=False
                )
                
                # Should have called ZoteroLibrary with API key from .env
                mock_zotero.assert_called_with("12345", api_key="abcdef1234567890abcdef78")
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["ZOTERO_API_KEY"] = original_env

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ZoteroLibrary")
    def test_cli_command_line_overrides_env(self, mock_zotero, mock_client):
        """Test that CLI command line --api-key overrides .env file."""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            # Create .env file
            Path(".env").write_text("ZOTERO_API_KEY=env1234567890abcdef1234\n")
            
            # Mock Zotero to check API key
            mock_zotero_instance = Mock()
            mock_zotero.return_value = mock_zotero_instance
            
            # Mock client
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.fetch_publications.return_value = []
            
            # Run command with --api-key
            result = runner.invoke(
                cli,
                [
                    "check",
                    "--orcid", "https://orcid.org/0000-0000-0000-0000",
                    "--zotero", "12345",
                    "--api-key", "abcdef1234567890abcdef90",
                ],
                catch_exceptions=False
            )
            
            # Should have called ZoteroLibrary with CLI API key
            mock_zotero.assert_called_with("12345", api_key="abcdef1234567890abcdef90")

    def test_env_file_with_multiple_variables(self):
        """Test loading .env file with multiple variables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .env file with multiple variables
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                "ZOTERO_API_KEY=zotero_key\n"
                "# Comment line\n"
                "OTHER_VAR=other_value\n"
                "EMPTY_VAR=\n"
            )
            
            # Mock current directory and clear environment
            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {}, clear=True):
                    env_vars = load_api_keys()
                    assert env_vars.get("ZOTERO_API_KEY") == "zotero_key"
                    assert env_vars.get("OTHER_VAR") == "other_value"
                    assert env_vars.get("EMPTY_VAR") == ""

    def test_env_file_with_quotes(self):
        """Test loading .env file with quoted values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .env file with quoted values
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(
                'ZOTERO_API_KEY="quoted_key"\n'
                "SINGLE_QUOTED='single_quoted_key'\n"
            )
            
            # Mock current directory and clear environment
            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {}, clear=True):
                    env_vars = load_api_keys()
                    # python-dotenv should handle quotes properly
                    assert env_vars.get("ZOTERO_API_KEY") == "quoted_key"
                    assert env_vars.get("SINGLE_QUOTED") == "single_quoted_key"