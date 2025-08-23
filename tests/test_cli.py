"""Tests for CLI interface."""

import pytest
from click.testing import CliRunner

from puby.cli import cli


class TestCLI:
    """Test CLI commands."""
    
    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Puby - Publication list management tool' in result.output
    
    def test_check_command_help(self):
        """Test check command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['check', '--help'])
        assert result.exit_code == 0
        assert '--orcid' in result.output
        assert '--scholar' in result.output
        assert '--zotero' in result.output
    
    def test_check_missing_source(self):
        """Test check command without any source."""
        runner = CliRunner()
        result = runner.invoke(cli, ['check', '--zotero', '12345'])
        assert result.exit_code == 1
        assert 'At least one source URL' in result.output
    
    def test_check_missing_zotero(self):
        """Test check command without zotero."""
        runner = CliRunner()
        result = runner.invoke(cli, ['check', '--orcid', 'https://orcid.org/0000-0000-0000-0000'])
        assert result.exit_code == 2  # Click's missing required option exit code
    
    def test_check_invalid_orcid_url(self):
        """Test check command with invalid ORCID URL."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'check',
            '--orcid', 'not-an-orcid-url',
            '--zotero', '12345'
        ])
        assert result.exit_code == 1
        assert 'Invalid ORCID URL' in result.output
    
    def test_check_invalid_scholar_url(self):
        """Test check command with invalid Scholar URL."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'check',
            '--scholar', 'not-a-scholar-url',
            '--zotero', '12345'
        ])
        assert result.exit_code == 1
        assert 'Invalid Scholar URL' in result.output
    
    def test_check_invalid_pure_url(self):
        """Test check command with non-HTTPS Pure URL."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'check',
            '--pure', 'http://pure.example.com',
            '--zotero', '12345'
        ])
        assert result.exit_code == 1
        assert 'Pure URL must use HTTPS' in result.output
    
    def test_version(self):
        """Test version display."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '0.1.0' in result.output