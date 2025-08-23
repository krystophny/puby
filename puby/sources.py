"""Publication sources for fetching data."""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests
from pyzotero import zotero

from .models import Author, Publication, ZoteroConfig


class PublicationSource(ABC):
    """Abstract base class for publication sources."""

    @abstractmethod
    def fetch(self) -> List[Publication]:
        """Fetch publications from the source."""
        pass


class ORCIDSource(PublicationSource):
    """Fetch publications from ORCID."""

    def __init__(self, orcid_url: str):
        """Initialize ORCID source."""
        self.orcid_url = orcid_url
        self.orcid_id = self._extract_orcid_id(orcid_url)
        self.logger = logging.getLogger(__name__)
        self.api_base = "https://pub.orcid.org/v3.0"

    def _extract_orcid_id(self, url: str) -> str:
        """Extract ORCID ID from URL."""
        # Match pattern like 0000-0000-0000-0000 (last digit can be X)
        pattern = r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]"
        match = re.search(pattern, url)
        if match:
            return match.group()
        # If just the ID was provided
        if re.match(pattern, url):
            return url
        raise ValueError(f"Invalid ORCID URL or ID: {url}")

    def fetch(self) -> List[Publication]:
        """Fetch publications from ORCID API."""
        publications = []

        # Fetch works summary
        works_url = f"{self.api_base}/{self.orcid_id}/works"
        headers = {"Accept": "application/json"}

        try:
            response = requests.get(works_url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Get work summaries
            work_groups = data.get("group", [])

            for group in work_groups:
                work_summary = group.get("work-summary", [])
                if work_summary:
                    # Take the first summary (they should be duplicates)
                    summary = work_summary[0]

                    # Fetch detailed work data
                    put_code = summary.get("put-code")
                    if put_code:
                        work_detail = self._fetch_work_detail(put_code)
                        if work_detail:
                            pub = self._parse_work(work_detail)
                            if pub:
                                publications.append(pub)

        except requests.RequestException as e:
            self.logger.error(f"Error fetching ORCID data: {e}")

        return publications

    def _fetch_work_detail(self, put_code: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed work information."""
        url = f"{self.api_base}/{self.orcid_id}/work/{put_code}"
        headers = {"Accept": "application/json"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else None
        except requests.RequestException as e:
            self.logger.error(f"Error fetching work detail: {e}")
            return None

    def _extract_title(self, work: Dict[str, Any]) -> str:
        """Extract title from ORCID work data."""
        title_data = work.get("title", {})
        return title_data.get("title", {}).get("value", "")

    def _extract_year(self, work: Dict[str, Any]) -> Optional[int]:
        """Extract publication year from ORCID work data."""
        pub_date = work.get("publication-date", {})
        if pub_date:
            year_data = pub_date.get("year", {})
            if year_data:
                year = year_data.get("value")
                if year:
                    return int(year)
        return None

    def _extract_journal(self, work: Dict[str, Any]) -> Optional[str]:
        """Extract journal name from ORCID work data."""
        journal = work.get("journal-title", {})
        return journal.get("value", "") if journal else None

    def _extract_doi(self, work: Dict[str, Any]) -> Optional[str]:
        """Extract DOI from ORCID work data."""
        external_ids = work.get("external-ids", {}).get("external-id", [])
        for ext_id in external_ids:
            if ext_id.get("external-id-type") == "doi":
                return ext_id.get("external-id-value")
        return None

    def _extract_url(self, work: Dict[str, Any]) -> Optional[str]:
        """Extract URL from ORCID work data."""
        url = work.get("url", {})
        return url.get("value") if url else None

    def _extract_authors(self, work: Dict[str, Any]) -> List[Author]:
        """Extract authors from ORCID work data."""
        authors = []
        contributors = work.get("contributors", {}).get("contributor", [])
        for contributor in contributors:
            credit_name = contributor.get("credit-name", {})
            if credit_name:
                name = credit_name.get("value", "")
                if name:
                    authors.append(Author(name=name))

        # If no contributors, add a placeholder
        if not authors:
            authors = [Author(name="[Authors not available]")]
        
        return authors

    def _parse_work(self, work: Dict[str, Any]) -> Optional[Publication]:
        """Parse ORCID work data into Publication."""
        try:
            title = self._extract_title(work)
            if not title:
                return None

            year = self._extract_year(work)
            journal_name = self._extract_journal(work)
            doi = self._extract_doi(work)
            url_value = self._extract_url(work)
            authors = self._extract_authors(work)

            return Publication(
                title=title,
                authors=authors,
                year=year,
                journal=journal_name,
                doi=doi,
                url=url_value,
                source="ORCID",
                raw_data=work,
            )

        except Exception as e:
            self.logger.error(f"Error parsing ORCID work: {e}")
            return None


class ScholarSource(PublicationSource):
    """Fetch publications from Google Scholar."""

    def __init__(self, scholar_url: str):
        """Initialize Scholar source."""
        self.scholar_url = scholar_url
        self.logger = logging.getLogger(__name__)

    def fetch(self) -> List[Publication]:
        """Fetch publications from Google Scholar."""
        # Note: Google Scholar doesn't provide an official API
        # This would require web scraping which may violate ToS
        # For now, return empty list with a warning

        self.logger.warning(
            "Google Scholar scraping is not implemented. "
            "Consider using the scholarly library or manual export."
        )
        return []


class PureSource(PublicationSource):
    """Fetch publications from Pure research portal."""

    def __init__(self, pure_url: str):
        """Initialize Pure source."""
        self.pure_url = pure_url
        self.logger = logging.getLogger(__name__)

    def fetch(self) -> List[Publication]:
        """Fetch publications from Pure portal."""
        # Pure portals often have APIs but they vary by institution
        # This would need institution-specific implementation

        self.logger.warning(
            "Pure portal integration not yet implemented. "
            "Pure APIs vary by institution."
        )
        return []


class ZoteroLibrary(PublicationSource):
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
            self.logger.error(f"Error fetching Zotero data: {e}")

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


class ZoteroSource(PublicationSource):
    """Modern Zotero API client using ZoteroConfig."""

    def __init__(self, config: ZoteroConfig):
        """Initialize Zotero source with configuration."""
        if not config.is_valid():
            errors = ", ".join(config.validation_errors())
            raise ValueError(f"Invalid Zotero configuration: {errors}")

        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize Zotero API client
        try:
            if self.config.library_type == "group":
                if not self.config.group_id:
                    raise ValueError("Group ID required for group library type")
                library_id = self.config.group_id
            else:
                # For user libraries, use group_id field as user_id
                # If no user_id provided, we cannot proceed (pyzotero needs explicit user ID)
                if not self.config.group_id:
                    raise ValueError(
                        "User ID is required for user library type. "
                        "Please provide your numeric user ID in the group_id field."
                    )
                library_id = self.config.group_id

            self.zot = zotero.Zotero(
                library_id, self.config.library_type, self.config.api_key
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Zotero client: {e}") from e

    def fetch(self) -> List[Publication]:
        """Fetch publications from Zotero library with pagination support."""
        publications = []

        try:
            # Use everything() to handle pagination automatically
            # This fetches all items in batches, handling Zotero's pagination
            items = self.zot.everything(self.zot.top())

            self.logger.info(f"Retrieved {len(items)} items from Zotero")

            for item in items:
                pub = self._parse_zotero_item(item)
                if pub:
                    publications.append(pub)

        except Exception as e:
            self.logger.error(f"Error fetching Zotero data: {e}")
            return []

        self.logger.info(f"Parsed {len(publications)} publications from Zotero")
        return publications

    def _is_publication_item(self, item_type: str) -> bool:
        """Check if Zotero item type represents a publication."""
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

    def _parse_zotero_creators(self, data: Dict[str, Any]) -> List[Author]:
        """Extract and parse authors from Zotero creators data."""
        authors = []
        creators = data.get("creators", [])
        for creator in creators:
            if creator.get("creatorType") == "author":
                first_name = creator.get("firstName", "").strip()
                last_name = creator.get("lastName", "").strip()

                if last_name or first_name:
                    full_name = f"{first_name} {last_name}".strip()
                    authors.append(
                        Author(
                            name=full_name,
                            given_name=first_name or None,
                            family_name=last_name or None,
                        )
                    )

        return authors if authors else [Author(name="[No authors]")]

    def _parse_publication_year(self, date_str: str) -> Optional[int]:
        """Parse publication year from Zotero date field."""
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

            if not self._is_publication_item(item_type):
                return None

            title = data.get("title", "").strip()
            if not title:
                return None

            authors = self._parse_zotero_creators(data)
            year = self._parse_publication_year(data.get("date", ""))

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
