"""Tests for CLI interface."""

from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import pytest

from puby.cli import cli
from puby.models import Publication, Author
from puby.matcher import PotentialMatch


class TestCLI:
    """Test CLI commands and integration."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Puby - Publication list management tool" in result.output

    def test_check_command_help(self):
        """Test check command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["check", "--help"])
        assert result.exit_code == 0
        assert "--orcid" in result.output
        assert "--scholar" in result.output
        assert "--zotero" in result.output

    def test_check_missing_source(self):
        """Test check command without any source."""
        runner = CliRunner()
        result = runner.invoke(cli, ["check", "--zotero", "12345"])
        assert result.exit_code == 1
        assert "At least one source URL" in result.output

    def test_check_missing_zotero(self):
        """Test check command without zotero."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["check", "--orcid", "https://orcid.org/0000-0000-0000-0000"]
        )
        assert result.exit_code == 2  # Click's missing required option exit code

    def test_check_invalid_orcid_url(self):
        """Test check command with invalid ORCID URL."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["check", "--orcid", "not-an-orcid-url", "--zotero", "12345"]
        )
        assert result.exit_code == 1
        assert "Invalid ORCID URL" in result.output

    def test_check_invalid_scholar_url(self):
        """Test check command with invalid Scholar URL."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["check", "--scholar", "not-a-scholar-url", "--zotero", "12345"]
        )
        assert result.exit_code == 1
        assert "Invalid Scholar URL" in result.output

    def test_check_invalid_pure_url(self):
        """Test check command with non-HTTPS Pure URL."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["check", "--pure", "http://pure.example.com", "--zotero", "12345"]
        )
        assert result.exit_code == 1
        assert "Pure URL must use HTTPS" in result.output

    def test_version(self):
        """Test version display."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    @patch('puby.cli.PublicationClient')
    @patch('puby.cli.ORCIDSource')
    @patch('puby.cli.ZoteroLibrary')
    def test_check_command_integration_success(
        self, mock_zotero_lib, mock_orcid_source, mock_client
    ):
        """Test successful end-to-end check command integration."""
        # Setup mock publications
        mock_pub1 = Publication(
            title="Test Paper 1",
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/test1"
        )
        mock_pub2 = Publication(
            title="Test Paper 2",
            authors=[Author(name="Jane Smith")],
            year=2023,
            doi="10.1000/test2"
        )
        mock_pub3 = Publication(
            title="Test Paper 1",  # Duplicate of mock_pub1
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/test1"
        )
        
        # Configure mocks
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub1, mock_pub2],  # ORCID publications
            [mock_pub3]  # Zotero publications (has duplicate)
        ]
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            "check",
            "--orcid", "https://orcid.org/0000-0000-0000-0000",
            "--zotero", "12345",
            "--api-key", "test-key",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        assert "Fetching publications from sources" in result.output
        assert "Analyzing publications" in result.output
        assert "Summary:" in result.output
        
        # Verify client was called correctly
        mock_client.assert_called_once_with(verbose=True)
        assert mock_client_instance.fetch_publications.call_count == 2

    @patch('puby.cli.PublicationClient')
    @patch('puby.cli.ORCIDSource')
    @patch('puby.cli.ZoteroLibrary')
    def test_check_command_with_missing_publications(
        self, mock_zotero_lib, mock_orcid_source, mock_client
    ):
        """Test check command identifies missing publications."""
        # ORCID has publications that Zotero doesn't
        orcid_pub = Publication(
            title="Missing Paper",
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/missing"
        )
        
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [orcid_pub],  # ORCID has publication
            []  # Zotero is empty
        ]
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            "check",
            "--orcid", "https://orcid.org/0000-0000-0000-0000",
            "--zotero", "12345"
        ])
        
        assert result.exit_code == 0
        assert "Missing from Zotero: 1" in result.output

    @patch('puby.cli.PublicationClient')
    @patch('puby.cli.ORCIDSource')
    @patch('puby.cli.ZoteroLibrary')
    def test_check_command_different_output_formats(
        self, mock_zotero_lib, mock_orcid_source, mock_client
    ):
        """Test check command with different output formats."""
        mock_pub = Publication(
            title="Test Paper",
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/test"
        )
        
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub],  # ORCID
            []  # Zotero empty
        ]
        
        # Test JSON format
        runner = CliRunner()
        result = runner.invoke(cli, [
            "check",
            "--orcid", "https://orcid.org/0000-0000-0000-0000",
            "--zotero", "12345",
            "--format", "json"
        ])
        
        assert result.exit_code == 0
        assert "Summary:" in result.output  # Summary always shown

    @patch('puby.cli.PublicationClient')
    def test_check_command_source_fetch_error(
        self, mock_client
    ):
        """Test check command handles source fetch errors gracefully."""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        # Simulate source fetch returning empty list (error handled in client)
        mock_client_instance.fetch_publications.return_value = []
        
        with patch('puby.cli._initialize_zotero') as mock_init_zotero:
            mock_zotero_lib = Mock()
            mock_init_zotero.return_value = mock_zotero_lib
            
            runner = CliRunner()
            result = runner.invoke(cli, [
                "check",
                "--orcid", "https://orcid.org/0000-0000-0000-0000",
                "--zotero", "12345"
            ])
            
            assert result.exit_code == 0  # Should not crash
            assert "Total publications in sources: 0" in result.output

    def test_check_command_zotero_initialization_error(self):
        """Test check command handles Zotero initialization errors."""
        with patch('puby.cli.ZoteroLibrary') as mock_zotero_lib:
            mock_zotero_lib.side_effect = ValueError("Invalid Zotero configuration")
            
            runner = CliRunner()
            result = runner.invoke(cli, [
                "check",
                "--orcid", "https://orcid.org/0000-0000-0000-0000",
                "--zotero", "invalid"
            ])
            
            assert result.exit_code == 1
            assert "Error: Invalid Zotero configuration" in result.output

    @patch('puby.cli.PublicationClient')
    @patch('puby.cli.ORCIDSource')
    @patch('puby.cli.ZoteroLibrary')
    @patch('puby.cli.ScholarSource')
    def test_check_command_multiple_sources(
        self, mock_scholar_source, mock_zotero_lib, mock_orcid_source, mock_client
    ):
        """Test check command with multiple publication sources."""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        # Need 3 calls: Scholar, ORCID, then Zotero
        mock_client_instance.fetch_publications.side_effect = [
            [Publication(title="Scholar Pub", authors=[], year=2023)],  # Scholar
            [Publication(title="ORCID Pub", authors=[], year=2023)],    # ORCID  
            [Publication(title="Zotero Pub", authors=[], year=2023)]    # Zotero
        ]
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            "check",
            "--orcid", "https://orcid.org/0000-0000-0000-0000",
            "--scholar", "https://scholar.google.com/citations?user=test",
            "--zotero", "12345",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        assert "Fetching from MagicMock" in result.output  # Mock sources show as MagicMock
        assert "Summary:" in result.output
        assert "Total publications in sources: 2" in result.output

    def test_fetch_command_help(self):
        """Test fetch command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["fetch", "--help"])
        assert result.exit_code == 0
        assert "--orcid" in result.output
        assert "--output" in result.output

    def test_fetch_command_missing_orcid(self):
        """Test fetch command without ORCID."""
        runner = CliRunner()
        result = runner.invoke(cli, ["fetch"])
        assert result.exit_code == 1
        assert "--orcid is required" in result.output

    @patch('puby.cli.PublicationClient')
    @patch('puby.cli.ORCIDSource')
    def test_fetch_command_success(self, mock_orcid_source, mock_client):
        """Test successful fetch command."""
        mock_pub = Publication(
            title="Test Paper",
            authors=[Author(name="John Doe")],
            year=2023
        )
        
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.return_value = [mock_pub]
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            "fetch",
            "--orcid", "https://orcid.org/0000-0000-0000-0000",
            "--output", "test.bib"
        ])
        
        assert result.exit_code == 0
        assert "Found 1 publications" in result.output
        assert "Saving to test.bib" in result.output
