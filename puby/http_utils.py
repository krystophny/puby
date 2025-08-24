"""HTTP utilities for consistent header handling and session management across sources."""

import random
from typing import Dict

import requests

from .http_session import get_shared_session


# Common User-Agent strings for different platforms
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]


def get_default_headers() -> Dict[str, str]:
    """Get default HTTP headers with consistent User-Agent.
    
    Returns:
        Dictionary of HTTP headers with a consistent User-Agent string.
        Suitable for sources that don't need User-Agent rotation.
    """
    return {
        "User-Agent": USER_AGENTS[0] if USER_AGENTS else "puby/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def get_headers_with_random_user_agent() -> Dict[str, str]:
    """Get HTTP headers with randomly selected User-Agent.
    
    Returns:
        Dictionary of HTTP headers with a randomly selected User-Agent string.
        Suitable for sources that benefit from User-Agent rotation (e.g., Scholar).
    """
    headers = get_default_headers()
    
    if USER_AGENTS:
        headers["User-Agent"] = random.choice(USER_AGENTS)
    
    return headers


def get_session_for_url(url: str) -> requests.Session:
    """Get a shared session configured for the specified URL.
    
    This function provides a session with connection pooling enabled,
    which dramatically improves performance for multiple requests to
    the same domain.
    
    Args:
        url: The URL to get a session for
        
    Returns:
        Configured requests.Session with connection pooling
        
    Example:
        >>> session = get_session_for_url('https://api.example.com/data')
        >>> response = session.get('https://api.example.com/users')
    """
    return get_shared_session(url)