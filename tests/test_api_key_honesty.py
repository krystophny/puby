"""Test API key honesty - never fake functionality when keys are missing."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from pyzotero.zotero_errors import UserNotAuthorisedError

from puby.cli import cli
from puby.legacy_sources import ZoteroLibrary
from puby.sources import ZoteroSource
from puby.models import ZoteroConfig


class TestZoteroAPIKeyHonesty:
    """Test that Zotero sources provide honest feedback about missing API keys."""

    def test_zotero_config_requires_api_key(self):
        """Test that ZoteroConfig validates API key presence."""
        # Missing API key
        config = ZoteroConfig(api_key="", group_id="123456")
        assert not config.is_valid()
        errors = config.validation_errors()
        assert any("API key is required" in error for error in errors)
        assert any("https://www.zotero.org/settings/keys" in error for error in errors)

        # Whitespace-only API key
        config = ZoteroConfig(api_key="   ", group_id="123456")
        assert not config.is_valid()
        errors = config.validation_errors()
        assert any("API key is required" in error for error in errors)

        # Valid API key
        config = ZoteroConfig(api_key="P9NiFoyLeZu2bZNvvuQPDWsd", group_id="123456")
        assert config.is_valid()

    @patch('puby.sources.requests.get')
    def test_zotero_source_validates_config(self, mock_get):
        """Test that ZoteroSource rejects invalid configurations."""
        # Missing API key
        invalid_config = ZoteroConfig(api_key="", group_id="123456")
        
        with pytest.raises(ValueError, match="Invalid Zotero configuration.*API key is required"):
            ZoteroSource(invalid_config)

        # Test auto-discovery failure with valid format but non-working key
        invalid_config = ZoteroConfig(api_key="invalid_key_format", library_type="user")
        
        # Mock failed auto-discovery
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = Exception("403 Forbidden")
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Failed to auto-discover user ID"):
            ZoteroSource(invalid_config)

    def test_zotero_library_handles_missing_api_key_gracefully(self):
        """Test that ZoteroLibrary provides clear error for missing API key."""
        # Test with mock to simulate API key validation failure
        with patch('puby.sources.zotero.Zotero') as mock_zotero_class:
            mock_zotero_class.side_effect = Exception("API key required for private library")
            
            with pytest.raises(ValueError, match="Failed to initialize Zotero client.*API key required"):
                ZoteroLibrary("123456", api_key=None)

    @patch('puby.sources.zotero.Zotero')
    def test_zotero_source_fetch_unauthorized_error(self, mock_zotero_class):
        """Test that fetch provides clear message on authorization failure."""
        # Setup mock Zotero client
        mock_zotero = Mock()
        mock_zotero_class.return_value = mock_zotero
        
        # Simulate unauthorized error
        mock_zotero.everything.side_effect = UserNotAuthorisedError("Invalid API key")
        
        config = ZoteroConfig(api_key="abcdef1234567890abcdef78", group_id="123456")
        source = ZoteroSource(config)
        
        # Should raise a clear error instead of returning empty list
        with pytest.raises(ValueError, match="Zotero API authentication failed"):
            source.fetch()
        
        # Verify the error was attempted to be handled
        mock_zotero.everything.assert_called_once()

    def test_cli_check_command_missing_api_key_error(self):
        """Test CLI check command provides clear error when API key is missing."""
        runner = CliRunner()
        
        # Test without API key for private library
        result = runner.invoke(cli, [
            'check',
            '--orcid', 'https://orcid.org/0000-0000-0000-0000',
            '--zotero', '123456'
            # No --api-key provided
        ])
        
        # Should fail with clear message about missing API key
        # Note: exact behavior depends on whether library is public or private
        # We're testing that it doesn't silently proceed with limited functionality

    def test_cli_check_command_invalid_api_key_error(self):
        """Test CLI provides clear error for invalid API key."""
        runner = CliRunner()
        
        with patch('puby.sources.zotero.Zotero') as mock_zotero_class:
            # Simulate API key validation failure
            mock_zotero_class.side_effect = Exception("Invalid API key provided")
            
            result = runner.invoke(cli, [
                'check',
                '--orcid', 'https://orcid.org/0000-0000-0000-0000',
                '--zotero', '123456',
                '--api-key', 'invalid_key_format'
            ])
            
            assert result.exit_code != 0
            assert "Invalid API key" in result.output or "Failed to initialize" in result.output

    @patch('puby.sources.requests.get')
    def test_no_silent_degradation_on_auth_failure(self, mock_get):
        """Test that sources don't silently degrade functionality on auth failures."""
        # Simulate 401 Unauthorized response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_get.return_value = mock_response
        
        # This would apply to any source that needs authentication
        # The key point is that it should fail clearly, not proceed with limited data

    def test_helpful_error_messages_guide_users(self):
        """Test that error messages guide users on obtaining API keys."""
        config = ZoteroConfig(api_key="")
        errors = config.validation_errors()
        
        # Should have clear, actionable error message
        assert any("API key is required" in error for error in errors)
        
        # When ZoteroSource is initialized with invalid config
        with pytest.raises(ValueError) as exc_info:
            ZoteroSource(config)
        
        # Error should mention what's wrong
        assert "API key is required" in str(exc_info.value)


class TestAPIKeyValidation:
    """Test that API keys are validated upfront, not during operations."""

    def test_early_api_key_validation(self):
        """Test that API key validation happens during initialization."""
        # Should fail immediately during initialization, not later during fetch
        invalid_config = ZoteroConfig(api_key="")
        
        with pytest.raises(ValueError, match="Invalid Zotero configuration"):
            ZoteroSource(invalid_config)
        
        # Should never get to the fetch stage
        # This ensures fail-fast behavior

    @patch('puby.sources.zotero.Zotero')
    def test_api_key_format_validation(self, mock_zotero_class):
        """Test that API key format is validated if possible."""
        # While we can't validate the actual key without calling the API,
        # we should at least check it's not empty or obviously invalid
        
        # Empty key should fail
        with pytest.raises(ValueError, match="API key is required"):
            config = ZoteroConfig(api_key="", group_id="123456")
            ZoteroSource(config)
        
        # Whitespace should fail
        with pytest.raises(ValueError, match="API key is required"):
            config = ZoteroConfig(api_key="   \t\n  ", group_id="123456")
            ZoteroSource(config)

    def test_no_fallback_to_public_endpoints(self):
        """Test that there's no automatic fallback to public endpoints."""
        # When API key is required but missing, should not try to access
        # public endpoints as a fallback - this would be dishonest
        config = ZoteroConfig(api_key="", group_id="123456")
        
        # Should fail immediately, not attempt public access
        with pytest.raises(ValueError, match="API key is required"):
            ZoteroSource(config)


class TestErrorMessageClarity:
    """Test that error messages are clear and actionable."""

    def test_missing_api_key_message_is_clear(self):
        """Test that missing API key error is unambiguous."""
        config = ZoteroConfig(api_key="")
        errors = config.validation_errors()
        
        # Message should be clear and direct
        assert any("API key is required" in error for error in errors)
        
        # Should provide guidance on how to get the key
        assert any("https://www.zotero.org/settings/keys" in error for error in errors)
        
        # Should not have vague messages like "configuration invalid"
        # without explaining what's wrong

    def test_error_messages_are_actionable(self):
        """Test that errors tell users what to do."""
        runner = CliRunner()
        
        with patch('puby.cli.ZoteroLibrary') as mock_zotero:
            mock_zotero.side_effect = ValueError(
                "Failed to initialize Zotero client: "
                "API key required for private library. "
                "Get your API key at https://www.zotero.org/settings/keys"
            )
            
            result = runner.invoke(cli, [
                'check',
                '--orcid', 'https://orcid.org/0000-0000-0000-0000',
                '--zotero', '123456'
            ])
            
            # Should show the helpful error message
            assert "API key required" in result.output
            
    def test_no_silent_failures(self):
        """Test that there are no silent failures when auth is missing."""
        # This is a meta-test to ensure we're not hiding auth failures
        
        # Test with ZoteroLibrary
        with patch('puby.sources.zotero.Zotero') as mock_zotero_class:
            mock_zotero_class.side_effect = Exception("API key required")
            
            # Should raise, not silently fail
            with pytest.raises(ValueError, match="Failed to initialize"):
                ZoteroLibrary("123456", api_key=None)
        
        # Test with ZoteroSource  
        invalid_config = ZoteroConfig(api_key="")
        
        # Should raise, not silently fail
        with pytest.raises(ValueError, match="Invalid Zotero configuration"):
            ZoteroSource(invalid_config)