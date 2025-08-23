"""Main client for fetching publications."""

import logging
from typing import List

from .models import Publication
from .sources import PublicationSource


class PublicationClient:
    """Client for managing publication fetching and processing."""

    def __init__(self, verbose: bool = False):
        """Initialize the publication client."""
        self.verbose = verbose
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def fetch_publications(self, source: PublicationSource) -> List[Publication]:
        """Fetch publications from a given source."""
        try:
            self.logger.debug(f"Fetching publications from {source.__class__.__name__}")
            publications = source.fetch()
            self.logger.info(
                f"Fetched {len(publications)} publications from {source.__class__.__name__}"
            )
            return publications
        except Exception as e:
            self.logger.error(f"Error fetching publications: {e}")
            return []
