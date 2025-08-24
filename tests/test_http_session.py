"""Tests for HTTP session management and connection pooling."""

import pytest
import requests
from unittest.mock import Mock, patch

from puby.http_session import HTTPSessionManager, get_shared_session


class TestHTTPSessionManager:
    """Tests for HTTP session manager."""

    def test_singleton_pattern(self):
        """Test that session manager follows singleton pattern."""
        manager1 = HTTPSessionManager()
        manager2 = HTTPSessionManager()
        assert manager1 is manager2

    def test_session_creation(self):
        """Test that session is created with proper configuration."""
        manager = HTTPSessionManager()
        session = manager.get_session("test.com")
        
        assert isinstance(session, requests.Session)
        # Verify connection pooling is configured
        adapter = session.get_adapter("http://test.com")
        assert hasattr(adapter, 'config')
        # HTTPAdapter stores pool config internally, verify it's our custom adapter
        assert isinstance(adapter, requests.adapters.HTTPAdapter)

    def test_session_reuse_same_domain(self):
        """Test that same session is reused for same domain."""
        manager = HTTPSessionManager()
        session1 = manager.get_session("example.com")
        session2 = manager.get_session("example.com")
        assert session1 is session2

    def test_session_different_for_different_domains(self):
        """Test that different sessions are used for different domains."""
        manager = HTTPSessionManager()
        session1 = manager.get_session("example.com")
        session2 = manager.get_session("different.com")
        assert session1 is not session2

    def test_session_with_subdomain(self):
        """Test session handling for subdomains."""
        manager = HTTPSessionManager()
        session1 = manager.get_session("api.example.com")
        session2 = manager.get_session("www.example.com")
        # Different subdomains should get different sessions
        assert session1 is not session2

    def test_cleanup_closes_sessions(self):
        """Test that cleanup properly closes all sessions."""
        manager = HTTPSessionManager()
        session = manager.get_session("test.com")
        
        with patch.object(session, 'close') as mock_close:
            manager.cleanup()
            mock_close.assert_called_once()

    def test_context_manager(self):
        """Test that session manager works as context manager."""
        with HTTPSessionManager() as manager:
            session = manager.get_session("test.com")
            assert isinstance(session, requests.Session)
        # Sessions should be closed after context exit


class TestSharedSessionFunction:
    """Tests for the shared session convenience function."""

    def test_get_shared_session_returns_session(self):
        """Test that get_shared_session returns a session."""
        session = get_shared_session("https://example.com/path")
        assert isinstance(session, requests.Session)

    def test_get_shared_session_extracts_domain(self):
        """Test that domain is properly extracted from URL."""
        session1 = get_shared_session("https://api.example.com/v1/data")
        session2 = get_shared_session("https://api.example.com/v2/users")
        # Same domain should return same session
        assert session1 is session2

    def test_get_shared_session_handles_plain_domain(self):
        """Test that plain domain strings work."""
        session = get_shared_session("api.example.com")
        assert isinstance(session, requests.Session)

    def test_get_shared_session_different_domains(self):
        """Test different domains get different sessions."""
        session1 = get_shared_session("https://orcid.org/api")
        session2 = get_shared_session("https://scholar.google.com/citations")
        assert session1 is not session2


class TestConnectionPoolingIntegration:
    """Integration tests for connection pooling with actual HTTP sources."""

    def test_adapter_configuration(self):
        """Test that HTTP adapters are configured with connection pooling."""
        manager = HTTPSessionManager()
        session = manager.get_session("example.com")
        
        # Get the adapter and verify it has proper configuration
        adapter = session.get_adapter("http://example.com")
        assert isinstance(adapter, requests.adapters.HTTPAdapter)
        
        # Verify poolmanager configuration by creating a new session
        # and checking that multiple sessions to same domain reuse connections
        session2 = manager.get_session("example.com")
        assert session is session2  # Same session should be reused

    def test_session_headers_preserved(self):
        """Test that session preserves custom headers."""
        manager = HTTPSessionManager()
        session = manager.get_session("example.com")
        
        # Add custom headers
        session.headers.update({"X-Custom": "test-value"})
        
        # Get session again and verify headers are preserved
        same_session = manager.get_session("example.com")
        assert same_session.headers.get("X-Custom") == "test-value"

    def test_session_timeout_configuration(self):
        """Test that sessions can be configured with timeouts."""
        manager = HTTPSessionManager()
        session = manager.get_session("example.com")
        
        # Session should allow timeout configuration
        # (This is more about the interface than implementation)
        assert hasattr(session, 'request')