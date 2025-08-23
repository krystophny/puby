"""Publication sources for fetching data."""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests
from pyzotero import zotero

from .models import Author, Publication


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
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Error fetching work detail: {e}")
            return None

    def _parse_work(self, work: Dict[str, Any]) -> Optional[Publication]:
        """Parse ORCID work data into Publication."""
        try:
            # Extract title
            title_data = work.get("title", {})
            title = title_data.get("title", {}).get("value", "")

            if not title:
                return None

            # Extract year
            pub_date = work.get("publication-date", {})
            year = None
            if pub_date:
                year_data = pub_date.get("year", {})
                if year_data:
                    year = year_data.get("value")
                    if year:
                        year = int(year)

            # Extract journal
            journal = work.get("journal-title", {})
            journal_name = journal.get("value", "") if journal else None

            # Extract DOI
            doi = None
            external_ids = work.get("external-ids", {}).get("external-id", [])
            for ext_id in external_ids:
                if ext_id.get("external-id-type") == "doi":
                    doi = ext_id.get("external-id-value")
                    break

            # Extract URL
            url = work.get("url", {})
            url_value = url.get("value") if url else None

            # Parse contributors/authors
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
    """Fetch publications from Zotero library."""

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

    def _parse_zotero_item(self, item: Dict[str, Any]) -> Optional[Publication]:
        """Parse Zotero item into Publication."""
        try:
            data = item.get("data", {})

            # Skip non-publication items
            item_type = data.get("itemType", "")
            if item_type not in [
                "journalArticle",
                "book",
                "bookSection",
                "conferencePaper",
                "thesis",
                "report",
                "preprint",
            ]:
                return None

            # Extract basic fields
            title = data.get("title", "")
            if not title:
                return None

            # Extract authors
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

            # Extract publication details
            year = None
            date_str = data.get("date", "")
            if date_str:
                # Try to extract year from date string
                import re

                year_match = re.search(r"\d{4}", date_str)
                if year_match:
                    year = int(year_match.group())

            return Publication(
                title=title,
                authors=authors if authors else [Author(name="[No authors]")],
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
