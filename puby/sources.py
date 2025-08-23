"""Publication sources for fetching data."""

# Import base class
from .base import PublicationSource

# Import the separated source classes
from .orcid_source import ORCIDSource
from .pure_source import PureSource
from .scholar_source import ScholarSource
from .zotero_source import ZoteroSource


# Re-export source classes for backward compatibility
__all__ = [
    "PublicationSource",
    "ORCIDSource",
    "PureSource",
    "ScholarSource",
    "ZoteroSource",
]