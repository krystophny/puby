"""Puby - Publication list management tool for researchers."""

__version__ = "0.1.0"

from .client import PublicationClient
from .env import get_api_key, load_api_keys
from .matcher import PublicationMatcher
from .models import Author, Publication
from .sources import ORCIDSource, PureSource, ScholarSource, ZoteroLibrary

__all__ = [
    "Author",
    "ORCIDSource",
    "Publication",
    "PublicationClient",
    "PublicationMatcher",
    "PureSource",
    "ScholarSource",
    "ZoteroLibrary",
    "get_api_key",
    "load_api_keys",
]
