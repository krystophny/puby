"""Google Scholar source implementation for puby."""

# Import the base class (will be a circular import but Python handles it)
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup, Tag

from .models import Author, Publication


class PublicationSource(ABC):
    """Abstract base class for publication sources."""

    @abstractmethod
    def fetch(self) -> list:
        """Fetch publications from the source."""
        pass

    def _get_logger(self):
        """Get logger for this source."""
        return logging.getLogger(self.__class__.__name__)


class ScholarSource(PublicationSource):
    """Source for fetching publications from Google Scholar profiles."""

    def __init__(self, scholar_url: str):
        """Initialize Scholar source."""
        self.url = scholar_url.strip()
        self.logger = self._get_logger()
        self.user_id = self._extract_scholar_id(self.url)
        self.logger.info(f"Initialized Scholar source for user {self.user_id}")

    def _extract_scholar_id(self, url: str) -> str:
        """Extract Scholar user ID from URL or return direct ID."""
        if url.startswith("http"):
            # Extract from full URL
            # Format: https://scholar.google.com/citations?user=USER_ID
            if "user=" in url:
                return url.split("user=")[1].split("&")[0]
            else:
                # Try to extract from different URL formats
                parts = url.split("/")
                for i, part in enumerate(parts):
                    if part == "citations" and i + 1 < len(parts):
                        # Could be in next part
                        continue
                raise ValueError(f"Could not extract Scholar user ID from URL: {url}")
        else:
            # Assume it's a direct user ID
            return url

    def _build_url(self, start: int) -> str:
        """Build Scholar profile URL with pagination."""
        base_url = "https://scholar.google.com/citations"
        params = f"user={self.user_id}&cstart={start}&pagesize=100"
        return f"{base_url}?{params}"

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with proper User-Agent."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]

        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _apply_rate_limit(self) -> None:
        """Apply random delay to avoid being blocked."""
        # Random delay between 1-3 seconds
        delay = random.uniform(1.0, 3.0)
        time.sleep(delay)

    def fetch(self) -> List[Publication]:
        """Fetch publications from Google Scholar profile."""
        publications = []
        start = 0

        try:
            while True:
                url = self._build_url(start)
                self.logger.info(f"Fetching Scholar profile page: {url}")

                response = requests.get(url, headers=self._get_headers())
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                page_pubs = self._parse_publications_page(soup)

                if not page_pubs:
                    # No more publications found
                    break

                publications.extend(page_pubs)

                # Check if there are more pages
                if not self._has_next_page(soup):
                    break

                start += 100
                self._apply_rate_limit()

        except requests.RequestException as e:
            self.logger.error(f"Error fetching Google Scholar data: {e}")
            return []

        self.logger.info(f"Fetched {len(publications)} publications from Scholar")
        return publications

    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there are more pages to fetch."""
        next_button = soup.find("button", {"id": "gsc_bpf_next"})
        if next_button is None:
            return False

        # Check if button is disabled
        return "disabled" not in next_button.get("class", [])

    def _parse_publications_page(self, soup: BeautifulSoup) -> List[Publication]:
        """Parse publications from a single page."""
        publications = []

        # Find publication rows
        pub_table = soup.find("table", {"id": "gsc_a_t"})
        if not pub_table:
            return publications

        rows = pub_table.find_all("tr", {"class": "gsc_a_tr"})

        for row in rows:
            try:
                pub = self._parse_publication_row(row)
                if pub:
                    publications.append(pub)
            except Exception as e:
                self.logger.warning(f"Failed to parse Scholar publication row: {e}")
                continue

        return publications

    def _parse_publication_row(self, row: Union[Tag, Any]) -> Optional[Publication]:
        """Parse individual publication row."""
        try:
            title = self._extract_title_from_row(row)
            if not title:
                return None

            # Extract publication metadata from the title cell
            title_cell = row.find("td", {"class": "gsc_a_t"})
            if not title_cell:
                return None

            authors, journal, year = self._extract_publication_metadata(title_cell)

            # Try to get year from separate column if not found
            if not year:
                year = self._extract_year_from_column(row)

            return Publication(
                title=title,
                authors=authors or [Author(name="[No authors]")],
                year=year,
                journal=journal,
                source="Google Scholar",
                publication_type="article",
            )

        except Exception as e:
            self.logger.error(f"Error parsing Scholar publication row: {e}")
            return None

    def _extract_title_from_row(self, row: Union[Tag, Any]) -> Optional[str]:
        """Extract title from publication row."""
        title_link = row.find("a", {"class": "gsc_a_at"})
        if title_link:
            title = title_link.get_text(strip=True)
            if title:
                return title

        # Fallback: try to find title in the cell
        title_cell = row.find("td", {"class": "gsc_a_t"})
        if title_cell:
            # First line should be the title
            lines = title_cell.get_text("\n").split("\n")
            if lines:
                return lines[0].strip()

        return None

    def _extract_publication_metadata(
        self, title_cell: Union[Tag, Any]
    ) -> tuple[List[Author], Optional[str], Optional[int]]:
        """Extract authors, journal, and year from title cell."""
        # Get all text and split by lines
        cell_text = title_cell.get_text("\n", strip=True)
        lines = [line.strip() for line in cell_text.split("\n") if line.strip()]

        authors = []
        journal = None
        year = None

        # Process lines after title (first line)
        for line in lines[1:]:
            if not line:
                continue

            # Try to parse as author/journal/year line
            authors_temp, journal_temp, year_temp = self._parse_journal_and_year(line)

            if authors_temp:
                authors.extend(authors_temp)
            if journal_temp:
                journal = journal_temp
            if year_temp:
                year = year_temp

        return authors, journal, year

    def _extract_year_from_column(self, row: Union[Tag, Any]) -> Optional[int]:
        """Extract year from the year column."""
        year_cell = row.find("span", {"class": "gsc_a_h"})
        if year_cell:
            year_text = year_cell.get_text(strip=True)
            # Extract 4-digit year
            year_match = re.search(r"\b(19|20)\d{2}\b", year_text)
            if year_match:
                try:
                    return int(year_match.group())
                except ValueError:
                    pass
        return None

    def _parse_authors(self, author_text: str) -> List[Author]:
        """Parse authors from comma-separated text."""
        authors = []
        if author_text:
            # Split by comma and clean up
            author_names = [name.strip() for name in author_text.split(",")]
            for name in author_names:
                if name and not name.lower().startswith(("and", "&")):
                    authors.append(Author(name=name))
        return authors

    def _parse_journal_and_year(
        self, pub_info: str
    ) -> tuple[List[Author], Optional[str], Optional[int]]:
        """Parse journal name and year from publication info string."""
        authors = []
        journal = None
        year = None

        # Try to extract year first (4-digit number)
        year_match = re.search(r"\b(19|20)\d{2}\b", pub_info)
        if year_match:
            try:
                year = int(year_match.group())
                # Remove year from string for further processing
                pub_info = pub_info.replace(year_match.group(), "").strip()
            except ValueError:
                pass

        # The remaining text could be authors and journal
        # This is a simplified approach - Scholar's format varies
        if pub_info:
            # If it looks like a journal name (has common journal words)
            journal_indicators = [
                "journal",
                "proceedings",
                "conference",
                "review",
                "letters",
                "transactions",
            ]
            if any(indicator in pub_info.lower() for indicator in journal_indicators):
                journal = pub_info.strip()
            else:
                # Might be authors or a mix - for now, treat as journal
                # A more sophisticated parser would be needed for better results
                if "," in pub_info:
                    # Looks like authors (comma-separated)
                    authors = self._parse_authors(pub_info)
                else:
                    # Single author or journal name
                    if len(pub_info) > 50 or any(
                        word in pub_info.lower() for word in journal_indicators
                    ):
                        journal = pub_info.strip()
                    else:
                        authors = [Author(name=pub_info.strip())]

        return authors, journal, year
