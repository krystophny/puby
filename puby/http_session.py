"""HTTP session management with connection pooling for optimal performance.

This module provides a shared session manager that implements connection pooling
to avoid creating new HTTP connections for each request. This dramatically
improves performance when making multiple requests to the same domains.
"""

import logging
import threading
from typing import Dict
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter


class HTTPSessionManager:
    """Singleton session manager with connection pooling.
    
    Manages HTTP sessions per domain to enable connection reuse and pooling.
    Each domain gets its own session configured with connection pooling.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure singleton pattern for session manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize session manager if not already initialized."""
        if not getattr(self, '_initialized', False):
            self.logger = logging.getLogger(__name__)
            self._sessions: Dict[str, requests.Session] = {}
            self._session_lock = threading.Lock()
            self._initialized = True
            self.logger.debug("HTTPSessionManager initialized")
    
    def get_session(self, domain: str) -> requests.Session:
        """Get or create a session for the specified domain.
        
        Args:
            domain: Domain name (e.g., 'api.example.com' or 'https://api.example.com')
            
        Returns:
            Configured requests.Session with connection pooling enabled.
        """
        # Extract clean domain from URL if provided
        clean_domain = self._extract_domain(domain)
        
        with self._session_lock:
            if clean_domain not in self._sessions:
                self._sessions[clean_domain] = self._create_session(clean_domain)
                self.logger.debug(f"Created new HTTP session for domain: {clean_domain}")
            
            return self._sessions[clean_domain]
    
    def _extract_domain(self, url_or_domain: str) -> str:
        """Extract domain from URL or return clean domain string.
        
        Args:
            url_or_domain: Either a full URL or just a domain name
            
        Returns:
            Clean domain name without protocol or path
        """
        if url_or_domain.startswith(('http://', 'https://')):
            parsed = urlparse(url_or_domain)
            return parsed.netloc
        return url_or_domain.strip()
    
    def _create_session(self, domain: str) -> requests.Session:
        """Create a new session configured with connection pooling.
        
        Args:
            domain: Domain name for this session
            
        Returns:
            Configured requests.Session with optimized connection pooling
        """
        session = requests.Session()
        
        # Configure HTTP adapter with connection pooling
        # pool_connections: Number of connection pools to cache (per host)
        # pool_maxsize: Maximum number of connections to save in the pool
        adapter = HTTPAdapter(
            pool_connections=10,  # Cache pools for 10 different hosts
            pool_maxsize=20,      # Keep up to 20 connections per host
            max_retries=3,        # Retry failed requests up to 3 times
            pool_block=False      # Don't block when pool is full
        )
        
        # Mount adapter for both HTTP and HTTPS
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        self.logger.debug(
            f"Configured session for {domain} with "
            f"pool_connections=10, pool_maxsize=20"
        )
        
        return session
    
    def cleanup(self) -> None:
        """Close all sessions and clean up resources.
        
        Should be called when the application is shutting down or when
        you want to force cleanup of all HTTP connections.
        """
        with self._session_lock:
            for domain, session in self._sessions.items():
                try:
                    session.close()
                    self.logger.debug(f"Closed session for domain: {domain}")
                except Exception as e:
                    self.logger.warning(f"Error closing session for {domain}: {e}")
            
            self._sessions.clear()
            self.logger.info("All HTTP sessions cleaned up")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup sessions."""
        self.cleanup()


# Global session manager instance
_session_manager = HTTPSessionManager()


def get_shared_session(url_or_domain: str) -> requests.Session:
    """Get a shared session for the specified URL or domain.
    
    This is a convenience function that provides easy access to the shared
    session manager. The session returned will have connection pooling
    enabled and will be reused for subsequent requests to the same domain.
    
    Args:
        url_or_domain: Either a full URL or just a domain name
        
    Returns:
        Configured requests.Session with connection pooling enabled
        
    Example:
        >>> session = get_shared_session('https://api.example.com/data')
        >>> response = session.get('https://api.example.com/users')
        >>> # Same session will be reused for subsequent requests to api.example.com
    """
    return _session_manager.get_session(url_or_domain)


def cleanup_sessions() -> None:
    """Clean up all shared sessions.
    
    This function closes all shared sessions and clears the session cache.
    Useful for cleanup during application shutdown or testing.
    """
    _session_manager.cleanup()