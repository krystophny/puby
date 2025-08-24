"""Tests for HTTP utilities module."""

import pytest
from unittest.mock import patch
from puby.http_utils import (
    get_default_headers,
    get_headers_with_random_user_agent,
    USER_AGENTS
)


class TestUserAgents:
    """Test User-Agent constants."""

    def test_user_agents_list_exists(self):
        """Test that USER_AGENTS list is available."""
        assert isinstance(USER_AGENTS, list)
        assert len(USER_AGENTS) > 0

    def test_user_agents_are_valid_strings(self):
        """Test that all User-Agent strings are valid."""
        for ua in USER_AGENTS:
            assert isinstance(ua, str)
            assert len(ua) > 0
            assert "Mozilla" in ua
            assert "Chrome" in ua

    def test_user_agents_represent_different_platforms(self):
        """Test that User-Agent strings cover different platforms."""
        ua_text = " ".join(USER_AGENTS)
        # Should have different OS representations
        assert "Windows NT" in ua_text
        assert "Macintosh" in ua_text or "Mac OS X" in ua_text
        assert "Linux x86_64" in ua_text


class TestDefaultHeaders:
    """Test default header construction."""

    def test_get_default_headers_structure(self):
        """Test that default headers have expected structure."""
        headers = get_default_headers()
        
        assert isinstance(headers, dict)
        
        # Check required headers
        required_headers = [
            "User-Agent", "Accept", "Accept-Language", 
            "Accept-Encoding", "Connection", "Upgrade-Insecure-Requests"
        ]
        
        for header in required_headers:
            assert header in headers
            assert isinstance(headers[header], str)
            assert len(headers[header]) > 0

    def test_default_headers_user_agent(self):
        """Test that default User-Agent is from our list."""
        headers = get_default_headers()
        assert headers["User-Agent"] in USER_AGENTS

    def test_default_headers_accept_types(self):
        """Test Accept header includes expected MIME types."""
        headers = get_default_headers()
        accept = headers["Accept"]
        
        assert "text/html" in accept
        assert "application/xhtml+xml" in accept
        assert "application/xml" in accept

    def test_default_headers_encoding(self):
        """Test Accept-Encoding includes common encodings."""
        headers = get_default_headers()
        encoding = headers["Accept-Encoding"]
        
        assert "gzip" in encoding
        assert "deflate" in encoding

    def test_default_headers_consistent_values(self):
        """Test that multiple calls return consistent non-random values."""
        headers1 = get_default_headers()
        headers2 = get_default_headers()
        
        # All headers except User-Agent should be identical
        for key in headers1:
            if key != "User-Agent":
                assert headers1[key] == headers2[key]


class TestRandomUserAgentHeaders:
    """Test random User-Agent header construction."""

    def test_random_headers_structure(self):
        """Test that random headers have expected structure."""
        headers = get_headers_with_random_user_agent()
        
        assert isinstance(headers, dict)
        
        # Should have same keys as default headers
        default_headers = get_default_headers()
        assert set(headers.keys()) == set(default_headers.keys())

    def test_random_user_agent_selection(self):
        """Test that random User-Agent selection works."""
        # Mock random.choice to test selection
        with patch('puby.http_utils.random.choice') as mock_choice:
            mock_choice.return_value = "Test User Agent"
            
            headers = get_headers_with_random_user_agent()
            
            mock_choice.assert_called_once_with(USER_AGENTS)
            assert headers["User-Agent"] == "Test User Agent"

    def test_random_user_agent_varies(self):
        """Test that User-Agent varies across calls (probabilistically)."""
        # With 3+ User-Agents, probability of getting same one 10 times is very low
        user_agents_seen = set()
        
        for _ in range(10):
            headers = get_headers_with_random_user_agent()
            user_agents_seen.add(headers["User-Agent"])
        
        # Should see at least 2 different User-Agents in 10 tries
        # (This could theoretically fail, but probability is extremely low)
        assert len(user_agents_seen) >= 2

    def test_random_headers_non_user_agent_consistent(self):
        """Test that non-User-Agent headers are consistent."""
        headers1 = get_headers_with_random_user_agent()
        headers2 = get_headers_with_random_user_agent()
        
        # All headers except User-Agent should be identical
        for key in headers1:
            if key != "User-Agent":
                assert headers1[key] == headers2[key]


class TestHeaderValues:
    """Test specific header values."""

    def test_accept_language_includes_english(self):
        """Test Accept-Language includes English preferences."""
        headers = get_default_headers()
        lang = headers["Accept-Language"]
        
        assert "en-US" in lang
        assert "en" in lang

    def test_connection_keep_alive(self):
        """Test Connection header is keep-alive."""
        headers = get_default_headers()
        assert headers["Connection"] == "keep-alive"

    def test_upgrade_insecure_requests(self):
        """Test Upgrade-Insecure-Requests header."""
        headers = get_default_headers()
        assert headers["Upgrade-Insecure-Requests"] == "1"


class TestHeaderConsistency:
    """Test consistency between different header functions."""

    def test_default_and_random_headers_same_structure(self):
        """Test that default and random headers have same keys."""
        default_headers = get_default_headers()
        random_headers = get_headers_with_random_user_agent()
        
        assert set(default_headers.keys()) == set(random_headers.keys())

    def test_default_and_random_headers_same_non_ua_values(self):
        """Test that non-User-Agent values are identical."""
        default_headers = get_default_headers()
        random_headers = get_headers_with_random_user_agent()
        
        for key in default_headers:
            if key != "User-Agent":
                assert default_headers[key] == random_headers[key]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_user_agents_list_handling(self):
        """Test behavior with empty USER_AGENTS list."""
        with patch('puby.http_utils.USER_AGENTS', []):
            # Should handle gracefully - either use fallback or raise clear error
            try:
                headers = get_default_headers()
                # If it succeeds, User-Agent should be some fallback value
                assert "User-Agent" in headers
                assert isinstance(headers["User-Agent"], str)
                assert len(headers["User-Agent"]) > 0
            except (IndexError, ValueError):
                # Acceptable to raise clear error for empty list
                pass

    def test_malformed_user_agents_filtering(self):
        """Test that malformed User-Agents are handled."""
        # This test verifies our USER_AGENTS list doesn't contain obviously bad values
        for ua in USER_AGENTS:
            # Should not be empty or just whitespace
            assert ua.strip() == ua
            assert len(ua.strip()) > 10  # Reasonable minimum length
            
            # Should not contain obvious problems
            assert "\n" not in ua
            assert "\r" not in ua
            assert "\t" not in ua