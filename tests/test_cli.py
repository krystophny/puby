"""Tests for CLI interface."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from puby.cli import cli
from puby.models import Author, Publication, ZoteroConfig


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
        assert result.exit_code == 1  # Validation error exit code
        assert "--zotero is required for group library type" in result.output

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

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_integration_success(
        self, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test successful end-to-end check command integration."""
        # Setup mock publications
        mock_pub1 = Publication(
            title="Test Paper 1",
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/test1",
        )
        mock_pub2 = Publication(
            title="Test Paper 2",
            authors=[Author(name="Jane Smith")],
            year=2023,
            doi="10.1000/test2",
        )
        mock_pub3 = Publication(
            title="Test Paper 1",  # Duplicate of mock_pub1
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/test1",
        )

        # Configure mocks
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub1, mock_pub2],  # ORCID publications
            [mock_pub3],  # Zotero publications (has duplicate)
        ]
        
        # Mock ZoteroSource instance
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
                "--api-key",
                "abcdef1234567890abcdef12",  # Valid 24-character API key format
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert "Fetching publications from sources" in result.output
        assert "Analyzing publications" in result.output
        assert "Summary:" in result.output

        # Verify client was called correctly
        mock_client.assert_called_once_with(verbose=True)
        assert mock_client_instance.fetch_publications.call_count == 2

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_with_missing_publications(
        self, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test check command identifies missing publications."""
        # ORCID has publications that Zotero doesn't
        orcid_pub = Publication(
            title="Missing Paper",
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/missing",
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [orcid_pub],  # ORCID has publication
            [],  # Zotero is empty
        ]
        
        # Mock ZoteroSource instance
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
            ],
        )

        assert result.exit_code == 0
        assert "Missing from Zotero: 1" in result.output

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_different_output_formats(
        self, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test check command with different output formats."""
        mock_pub = Publication(
            title="Test Paper",
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/test",
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub],  # ORCID
            [],  # Zotero empty
        ]
        
        # Mock ZoteroSource instance
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        # Test JSON format
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        assert "Summary:" in result.output  # Summary always shown

    @patch("puby.cli.PublicationClient")
    def test_check_command_source_fetch_error(self, mock_client):
        """Test check command handles source fetch errors gracefully."""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        # Simulate source fetch returning empty list (error handled in client)
        mock_client_instance.fetch_publications.return_value = []

        with patch("puby.cli._initialize_zotero") as mock_init_zotero:
            mock_zotero_lib = Mock()
            mock_init_zotero.return_value = mock_zotero_lib

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "check",
                    "--orcid",
                    "https://orcid.org/0000-0000-0000-0000",
                    "--zotero",
                    "12345",
                ],
            )

            assert result.exit_code == 0  # Should not crash
            assert "Total publications in sources: 0" in result.output

    def test_check_command_zotero_initialization_error(self):
        """Test check command handles Zotero initialization errors."""
        with patch("puby.cli.ZoteroSource") as mock_zotero_source:
            mock_zotero_source.side_effect = ValueError("Invalid Zotero configuration")

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "check",
                    "--orcid",
                    "https://orcid.org/0000-0000-0000-0000",
                    "--zotero",
                    "invalid",
                ],
            )

            assert result.exit_code == 1
            assert "Error: Invalid Zotero configuration" in result.output

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    @patch("puby.cli.ScholarSource")
    def test_check_command_multiple_sources(
        self, mock_scholar_source, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test check command with multiple publication sources."""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        # Need 3 calls: Scholar, ORCID, then Zotero
        mock_client_instance.fetch_publications.side_effect = [
            [Publication(title="Scholar Pub", authors=[], year=2023)],  # Scholar
            [Publication(title="ORCID Pub", authors=[], year=2023)],  # ORCID
            [Publication(title="Zotero Pub", authors=[], year=2023)],  # Zotero
        ]
        
        # Mock ZoteroSource instance
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--scholar",
                "https://scholar.google.com/citations?user=test",
                "--zotero",
                "12345",
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert (
            "Fetching from MagicMock" in result.output
        )  # Mock sources show as MagicMock
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

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    def test_fetch_command_success(self, mock_orcid_source, mock_client):
        """Test successful fetch command."""
        mock_pub = Publication(
            title="Test Paper", authors=[Author(name="John Doe")], year=2023
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.return_value = [mock_pub]

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "fetch",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--output",
                "test.bib",
            ],
        )

        assert result.exit_code == 0
        assert "Found 1 publications" in result.output
        assert "Successfully saved" in result.output
        assert "test.bib" in result.output


class TestCLIZoteroSourceIntegration:
    """Test CLI integration with ZoteroSource class."""

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_with_zotero_source_group_library(
        self, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test check command using ZoteroSource for group library."""
        # Setup mock publications
        mock_pub = Publication(
            title="Test Paper",
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/test",
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub],  # ORCID publications
            [mock_pub],  # Zotero publications
        ]

        # Mock ZoteroSource initialization
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
                "--zotero-library-type",
                "group",
                "--api-key",
                "abcdef1234567890abcdef12",
            ],
        )

        assert result.exit_code == 0
        # Verify ZoteroSource was initialized with correct config
        mock_zotero_source.assert_called_once()
        config_arg = mock_zotero_source.call_args[0][0]
        assert isinstance(config_arg, ZoteroConfig)
        assert config_arg.api_key == "abcdef1234567890abcdef12"
        assert config_arg.group_id == "12345"
        assert config_arg.library_type == "group"

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_with_zotero_source_user_library(
        self, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test check command using ZoteroSource for user library."""
        mock_pub = Publication(
            title="Test Paper",
            authors=[Author(name="John Doe")],
            year=2023,
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub],  # ORCID
            [mock_pub],  # Zotero
        ]

        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "user-id-123",
                "--zotero-library-type",
                "user",
                "--api-key",
                "abcdef1234567890abcdef12",
            ],
        )

        assert result.exit_code == 0
        # Verify ZoteroSource was initialized with user library config
        mock_zotero_source.assert_called_once()
        config_arg = mock_zotero_source.call_args[0][0]
        assert config_arg.library_type == "user"
        assert config_arg.group_id == "user-id-123"

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_zotero_source_auto_user_id_discovery(
        self, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test check command with ZoteroSource auto-discovering user ID."""
        mock_pub = Publication(
            title="Test Paper",
            authors=[Author(name="John Doe")],
            year=2023,
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub],  # ORCID
            [mock_pub],  # Zotero
        ]

        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero-library-type",
                "user",
                "--api-key",
                "abcdef1234567890abcdef12",
            ],
        )

        assert result.exit_code == 0
        # Verify ZoteroSource was initialized without explicit user ID
        # (will be auto-discovered)
        mock_zotero_source.assert_called_once()
        config_arg = mock_zotero_source.call_args[0][0]
        assert config_arg.library_type == "user"
        assert config_arg.group_id is None  # Will be auto-discovered

    @patch("puby.cli.ZoteroSource")
    def test_check_command_zotero_source_invalid_config(self, mock_zotero_source):
        """Test check command handles invalid ZoteroSource configuration."""
        # Mock ZoteroSource to raise ValueError for invalid config
        mock_zotero_source.side_effect = ValueError(
            "Invalid Zotero configuration: API key is required"
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
                "--zotero-library-type",
                "group",
                # No API key provided
            ],
        )

        assert result.exit_code == 1
        assert "Invalid Zotero configuration" in result.output

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_zotero_source_authentication_error(
        self, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test check command handles ZoteroSource authentication errors."""
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [Publication(title="Test", authors=[], year=2023)],  # ORCID success
            # Zotero fetch will fail via exception in source
        ]

        # Mock ZoteroSource instance that works for init but fails on fetch
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        # Mock fetch_publications to handle the ZoteroSource properly
        def mock_fetch_side_effect(source):
            if isinstance(source, type(mock_zotero_instance)):
                raise ValueError(
                    "Zotero API authentication failed. Please provide a valid API key."
                )
            return [Publication(title="Test", authors=[], year=2023)]

        mock_client_instance.fetch_publications.side_effect = mock_fetch_side_effect

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
                "--api-key",
                "invalidkey123456789012345",  # Valid format but invalid key
            ],
        )

        # Should show proper error handling
        assert result.exit_code == 1
        assert "Zotero API authentication failed" in result.output

    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_zotero_source_backward_compatibility(
        self, mock_zotero_source, mock_orcid_source, mock_client
    ):
        """Test that ZoteroSource integration maintains backward compatibility."""
        # This test ensures existing CLI commands still work
        mock_pub = Publication(
            title="Test Paper",
            authors=[Author(name="John Doe")],
            year=2023,
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub],  # ORCID
            [mock_pub],  # Zotero
        ]

        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        # Use old-style command without new options
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
                "--api-key",
                "abcdef1234567890abcdef12",
            ],
        )

        assert result.exit_code == 0
        assert "Summary:" in result.output
        # Should default to group library type for backward compatibility
        mock_zotero_source.assert_called_once()
        config_arg = mock_zotero_source.call_args[0][0]
        assert config_arg.library_type == "group"  # Default for backward compatibility

    @patch("puby.cli._export_missing_publications")
    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_with_export_missing(
        self, mock_zotero_source, mock_orcid_source, mock_client, mock_export
    ):
        """Test check command with --export-missing option."""
        # ORCID has publications that Zotero doesn't
        missing_pub = Publication(
            title="Missing Paper",
            authors=[Author(name="John Doe")],
            year=2023,
            doi="10.1000/missing",
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [missing_pub],  # ORCID has publication
            [],  # Zotero is empty
        ]
        
        # Mock ZoteroSource instance
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
                "--export-missing",
                "missing_pubs.bib",
            ],
        )

        assert result.exit_code == 0
        assert "Missing from Zotero: 1" in result.output
        assert "Exported 1 missing publications to missing_pubs.bib" in result.output
        
        # Verify export function was called with correct arguments
        mock_export.assert_called_once_with([missing_pub], "missing_pubs.bib")

    @patch("puby.cli._export_missing_publications")  
    @patch("puby.cli.PublicationClient")
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_export_missing_default_filename(
        self, mock_zotero_source, mock_orcid_source, mock_client, mock_export
    ):
        """Test check command with --export-missing using default filename."""
        missing_pub = Publication(
            title="Missing Paper",
            authors=[Author(name="John Doe")],
            year=2023,
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance  
        mock_client_instance.fetch_publications.side_effect = [
            [missing_pub],  # ORCID has publication
            [],  # Zotero is empty
        ]
        
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid", 
                "https://orcid.org/0000-0000-0000-0000",
                "--zotero",
                "12345",
                "--export-missing",
                "missing_publications.bib",  # Explicitly provide filename
            ],
        )

        assert result.exit_code == 0
        assert "Exported 1 missing publications to missing_publications.bib" in result.output
        
        # Should use provided filename
        mock_export.assert_called_once_with([missing_pub], "missing_publications.bib")

    @patch("puby.cli._export_missing_publications")
    @patch("puby.cli.PublicationClient") 
    @patch("puby.cli.ORCIDSource")
    @patch("puby.cli.ZoteroSource")
    def test_check_command_export_missing_no_missing_publications(
        self, mock_zotero_source, mock_orcid_source, mock_client, mock_export
    ):
        """Test check command with --export-missing when no publications are missing."""
        mock_pub = Publication(
            title="Existing Paper",
            authors=[Author(name="John Doe")],
            year=2023,
        )

        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_publications.side_effect = [
            [mock_pub],  # ORCID has publication
            [mock_pub],  # Zotero has same publication
        ]
        
        mock_zotero_instance = Mock()
        mock_zotero_source.return_value = mock_zotero_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "check",
                "--orcid",
                "https://orcid.org/0000-0000-0000-0000", 
                "--zotero",
                "12345",
                "--export-missing",
                "no_missing.bib",
            ],
        )

        assert result.exit_code == 0
        assert "Missing from Zotero: 0" in result.output
        assert "Exported 0 missing publications to no_missing.bib" in result.output
        
        # Should still call export with empty list
        mock_export.assert_called_once_with([], "no_missing.bib")
