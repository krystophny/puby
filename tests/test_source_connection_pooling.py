"""Integration tests for connection pooling in publication sources."""

import pytest
from unittest.mock import Mock, patch

from puby.orcid_source import ORCIDSource
from puby.pure_source import PureSource
from puby.scholar_source import ScholarSource
from puby.zotero_source import ZoteroSource
from puby.models import ZoteroConfig


class TestORCIDSourceConnectionPooling:
    """Test ORCID source uses connection pooling."""

    def test_orcid_uses_session(self):
        """Test that ORCID source initializes with session."""
        source = ORCIDSource("https://orcid.org/0000-0000-0000-0000")
        assert hasattr(source, '_session')
        assert source._session is not None

    @patch('puby.orcid_source.get_session_for_url')
    def test_orcid_gets_session_for_api_base(self, mock_get_session):
        """Test that ORCID source gets session for the API base URL."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        source = ORCIDSource("https://orcid.org/0000-0000-0000-0000")
        
        mock_get_session.assert_called_once_with("https://pub.orcid.org/v3.0")
        assert source._session is mock_session

    @patch('puby.orcid_source.get_session_for_url')
    def test_orcid_reuses_session_for_multiple_requests(self, mock_get_session):
        """Test that ORCID source reuses session for multiple API calls."""
        mock_session = Mock()
        mock_session.get.return_value.raise_for_status.return_value = None
        mock_session.get.return_value.json.return_value = {"group": []}
        mock_get_session.return_value = mock_session
        
        source = ORCIDSource("https://orcid.org/0000-0000-0000-0000")
        source.fetch()
        
        # Verify session.get was called instead of requests.get
        assert mock_session.get.called
        # Verify the session was obtained only once during initialization
        mock_get_session.assert_called_once()


class TestPureSourceConnectionPooling:
    """Test Pure source uses connection pooling."""

    def test_pure_uses_session(self):
        """Test that Pure source initializes with session."""
        source = PureSource("https://research.example.com/persons/123456")
        assert hasattr(source, '_session')
        assert source._session is not None

    @patch('puby.pure_source.get_session_for_url')
    def test_pure_gets_session_for_base_domain(self, mock_get_session):
        """Test that Pure source gets session for the base domain."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        source = PureSource("https://research.example.com/persons/123456")
        
        mock_get_session.assert_called_once_with("https://research.example.com")
        assert source._session is mock_session


class TestScholarSourceConnectionPooling:
    """Test Scholar source uses connection pooling."""

    def test_scholar_uses_session(self):
        """Test that Scholar source initializes with session."""
        source = ScholarSource("https://scholar.google.com/citations?user=TEST_USER")
        assert hasattr(source, '_session')
        assert source._session is not None

    @patch('puby.scholar_source.get_session_for_url')
    def test_scholar_gets_session_for_google_scholar(self, mock_get_session):
        """Test that Scholar source gets session for Google Scholar domain."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        source = ScholarSource("https://scholar.google.com/citations?user=TEST_USER")
        
        mock_get_session.assert_called_once_with("https://scholar.google.com")
        assert source._session is mock_session


class TestZoteroSourceConnectionPooling:
    """Test Zotero source uses connection pooling."""

    def test_zotero_uses_session(self):
        """Test that Zotero source initializes with session."""
        config = ZoteroConfig(
            api_key="abcdefgh1234567890123456",  # Valid 24-char alphanumeric key
            library_type="user",
            group_id="123456"
        )
        
        with patch('puby.zotero_source.zotero.Zotero'):
            with patch.object(ZoteroSource, 'validate_connection'):
                source = ZoteroSource(config)
                assert hasattr(source, '_session')
                assert source._session is not None

    @patch('puby.zotero_source.get_session_for_url')
    def test_zotero_gets_session_for_api_base(self, mock_get_session):
        """Test that Zotero source gets session for the API base URL."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        config = ZoteroConfig(
            api_key="abcdefgh1234567890123456",  # Valid 24-char alphanumeric key
            library_type="user",
            group_id="123456"
        )
        
        with patch('puby.zotero_source.zotero.Zotero'):
            with patch.object(ZoteroSource, 'validate_connection'):
                source = ZoteroSource(config)
        
        mock_get_session.assert_called_once_with("https://api.zotero.org")
        assert source._session is mock_session


class TestConnectionPoolingPerformance:
    """Performance and behavior tests for connection pooling."""

    @patch('puby.orcid_source.get_session_for_url')
    def test_multiple_sources_same_domain_share_session(self, mock_get_session):
        """Test that multiple sources for the same domain share sessions."""
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        # Create two ORCID sources - should share the same session
        source1 = ORCIDSource("https://orcid.org/0000-0000-0000-0001")
        source2 = ORCIDSource("https://orcid.org/0000-0000-0000-0002")
        
        # Both should get sessions for the same ORCID API base
        assert mock_get_session.call_count == 2
        assert source1._session is mock_session
        assert source2._session is mock_session

    def test_different_domains_get_different_sessions(self):
        """Test that different domains get different sessions."""
        orcid_source = ORCIDSource("https://orcid.org/0000-0000-0000-0000")
        scholar_source = ScholarSource("https://scholar.google.com/citations?user=TEST")
        
        # Different domains should have different session objects
        assert orcid_source._session is not scholar_source._session

    def test_session_reuse_within_source(self):
        """Test that a source reuses its session for multiple requests."""
        source = ORCIDSource("https://orcid.org/0000-0000-0000-0000")
        original_session = source._session
        
        # Multiple operations should reuse the same session
        with patch.object(source._session, 'get') as mock_get:
            mock_get.return_value.raise_for_status.return_value = None
            mock_get.return_value.json.return_value = {"group": []}
            
            source.fetch()
            
            # Session should remain the same
            assert source._session is original_session
            # Session.get should have been called
            assert mock_get.called