"""Legacy source implementations - maintained for backward compatibility."""

import logging
import re
from typing import Any, Dict, List, Optional

from pyzotero import zotero  # type: ignore

from .models import Author, Publication


class ZoteroLibrary:
    """Fetch publications from Zotero library.

    NOTE: This is legacy implementation. Use ZoteroSource instead for new code.
    """

    def __init__(self, library_id: str, api_key: Optional[str] = None):
        """Initialize Zotero library source."""
        self.library_id = library_id
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)

        # Determine if it's a group or user library
        self.library_type = "group"  # Default to group

        # Initialize Zotero API client
        try:
            if self.api_key:
                self.zot = zotero.Zotero(
                    self.library_id, self.library_type, self.api_key
                )
            else:
                # Public library access
                self.zot = zotero.Zotero(self.library_id, self.library_type)
        except Exception as e:
            # Provide helpful guidance for common authentication issues
            error_msg = str(e).lower()
            if any(term in error_msg for term in ['api key', 'auth', 'credentials', 'unauthorized']):
                raise ValueError(
                    f"Failed to initialize Zotero client: {e}. "
                    f"Please ensure you have a valid API key. "
                    f"Get your API key at: https://www.zotero.org/settings/keys"
                ) from e
            else:
                raise ValueError(f"Failed to initialize Zotero client: {e}") from e

    def fetch(self) -> List[Publication]:
        """Fetch publications from Zotero library."""
        publications = []

        try:
            # Fetch all items
            items = self.zot.everything(self.zot.top())

            for item in items:
                pub = self._parse_zotero_item(item)
                if pub:
                    publications.append(pub)

        except Exception as e:
            # Provide clear feedback for authentication issues
            error_msg = str(e).lower()
            if any(term in error_msg for term in ['auth', 'unauthorized', 'forbidden', 'api key', 'credentials']):
                self.logger.error(
                    f"Zotero authentication failed: {e}. "
                    f"Please check your API key is valid. "
                    f"Get your API key at: https://www.zotero.org/settings/keys"
                )
                raise ValueError(
                    f"Zotero API authentication failed. Please provide a valid API key. "
                    f"Get your API key at: https://www.zotero.org/settings/keys"
                ) from e
            else:
                self.logger.error(f"Error fetching Zotero data: {e}")
                raise ValueError(f"Failed to fetch Zotero data: {e}") from e

        return publications

    def _is_publication_type(self, item_type: str) -> bool:
        """Check if item type is a publication type."""
        publication_types = [
            "journalArticle",
            "book",
            "bookSection",
            "conferencePaper",
            "thesis",
            "report",
            "preprint",
        ]
        return item_type in publication_types

    def _extract_zotero_authors(self, data: Dict[str, Any]) -> List[Author]:
        """Extract authors from Zotero item data."""
        authors = []
        creators = data.get("creators", [])
        for creator in creators:
            if creator.get("creatorType") == "author":
                first_name = creator.get("firstName", "")
                last_name = creator.get("lastName", "")
                if last_name:
                    authors.append(
                        Author(
                            name=f"{first_name} {last_name}".strip(),
                            given_name=first_name,
                            family_name=last_name,
                        )
                    )
        return authors if authors else [Author(name="[No authors]")]

    def _extract_year_from_date(self, date_str: str) -> Optional[int]:
        """Extract year from date string."""
        if date_str:
            year_match = re.search(r"\d{4}", date_str)
            if year_match:
                return int(year_match.group())
        return None

    def _parse_zotero_item(self, item: Dict[str, Any]) -> Optional[Publication]:
        """Parse Zotero item into Publication."""
        try:
            data = item.get("data", {})
            item_type = data.get("itemType", "")

            if not self._is_publication_type(item_type):
                return None

            title = data.get("title", "")
            if not title:
                return None

            authors = self._extract_zotero_authors(data)
            year = self._extract_year_from_date(data.get("date", ""))

            return Publication(
                title=title,
                authors=authors,
                year=year,
                journal=data.get("publicationTitle"),
                volume=data.get("volume"),
                issue=data.get("issue"),
                pages=data.get("pages"),
                doi=data.get("DOI"),
                url=data.get("url"),
                abstract=data.get("abstractNote"),
                publication_type=item_type,
                source="Zotero",
                raw_data=data,
            )

        except Exception as e:
            self.logger.error(f"Error parsing Zotero item: {e}")
            return None