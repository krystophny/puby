"""Base classes for publication sources."""

from abc import ABC, abstractmethod
from typing import List

from .models import Publication


class PublicationSource(ABC):
    """Abstract base class for publication sources."""

    @abstractmethod
    def fetch(self) -> List[Publication]:
        """Fetch publications from the source."""
        pass