"""Puby - Publication list management tool for researchers."""

__version__ = "0.1.0"

from .client import PublicationClient
from .sources import ORCIDSource, ScholarSource, PureSource, ZoteroLibrary
from .matcher import PublicationMatcher
from .models import Publication, Author

__all__ = [
    "PublicationClient",
    "ORCIDSource",
    "ScholarSource", 
    "PureSource",
    "ZoteroLibrary",
    "PublicationMatcher",
    "Publication",
    "Author",
]