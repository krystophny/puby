"""Pure source implementation for puby."""

# Import the base class (will be a circular import but Python handles it)
import contextlib
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

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


class PureSource(PublicationSource):
    """Source for fetching publications from Pure research portals."""

    def __init__(self, pure_url: str):
        """Initialize Pure source with validation."""
        self.url = pure_url.strip()
        self.logger = self._get_logger()

        # Validate URL format
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(
                f"Pure URL must start with http:// or https://: {self.url}"
            )

        # Extract components
        self.base_domain = self._extract_base_domain()
        self.person_id = self._extract_person_id()

        self.logger.info(f"Initialized Pure source for {self.base_domain}")

    def _extract_base_domain(self) -> str:
        """Extract base domain from Pure URL."""
        parsed = urlparse(self.url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _extract_person_id(self) -> str:
        """Extract person identifier from Pure URL."""
        # Extract person ID from various Pure URL formats
        if "/persons/" in self.url:
            return self.url.split("/persons/")[-1].split("/")[0]
        else:
            raise ValueError(f"Could not extract person ID from Pure URL: {self.url}")

    def _build_api_url(self) -> str:
        """Build Pure API URL for research outputs."""
        return f"{self.base_domain}/ws/api/persons/{self.person_id}/research-outputs"

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with proper User-Agent."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _apply_rate_limit(self) -> None:
        """Apply delay to avoid overwhelming Pure portals."""
        # Be extra respectful to institutional Pure portals
        time.sleep(2.0)

    def fetch(self) -> List[Publication]:
        """Fetch publications from Pure portal.

        Attempts API access first, falls back to HTML scraping.
        """
        # Try API first if available
        try:
            api_url = self._build_api_url()
            self.logger.info(f"Trying Pure API: {api_url}")
            response = requests.get(api_url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                return self._parse_api_response(data)
        except Exception as e:
            self.logger.warning(f"Pure API failed, falling back to HTML scraping: {e}")

        # Fall back to HTML scraping
        return self._fetch_from_html()

    def _fetch_from_html(self) -> List[Publication]:
        """Fetch publications via HTML scraping with pagination support."""
        publications = []
        current_url = self.url
        max_pages = 10  # Safety limit
        page_count = 0

        try:
            while current_url and page_count < max_pages:
                self.logger.info(f"Fetching Pure page {page_count + 1}: {current_url}")

                response = requests.get(current_url, headers=self._get_headers())
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                page_pubs = self._parse_html_page(soup)

                if not page_pubs:
                    break

                publications.extend(page_pubs)

                # Look for next page
                next_url = self._find_next_page_url(soup)
                if next_url:
                    current_url = urljoin(current_url, next_url)
                else:
                    break

                page_count += 1
                self._apply_rate_limit()

        except requests.RequestException as e:
            self.logger.error(f"Error fetching Pure data: {e}")
            return []

        self.logger.info(f"Fetched {len(publications)} publications from Pure")
        return publications

    def _find_next_page_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Find URL for next page of results."""
        # Look for common Pure pagination patterns
        next_links = soup.find_all(
            "a", string=re.compile(r"next|Next|NEXT|Load more|>", re.IGNORECASE)
        )
        for link in next_links:
            href = link.get("href")
            if href:
                return href

        # Try numeric pagination
        page_links = soup.find_all("a", href=re.compile(r"page=\d+"))
        current_page = 1
        for link in page_links:
            href = link.get("href", "")
            if f"page={current_page + 1}" in href:
                return href

        return None

    def _parse_html_page(self, soup: BeautifulSoup) -> List[Publication]:
        """Parse publications from HTML page."""
        publications = []

        # Look for publication containers - Pure uses various CSS classes
        # First try to find individual publication items (more specific)
        containers = soup.find_all(
            ["div", "article"],
            class_=re.compile(r"rendering_contributiontojournal", re.IGNORECASE),
        )
        
        # If no specific containers found, try broader search
        if not containers:
            containers = soup.find_all(
                ["div", "article"],
                class_=re.compile(r"result|publication|research-output", re.IGNORECASE),
            )

        for container in containers:
            try:
                pub = self._parse_publication_container(container)
                if pub:
                    publications.append(pub)
            except Exception as e:
                self.logger.warning(f"Failed to parse Pure publication: {e}")
                continue

        return publications

    def _parse_publication_container(
        self, container: BeautifulSoup
    ) -> Optional[Publication]:
        """Parse individual publication container."""
        try:
            title = self._extract_title_from_container(container)
            if not title:
                return None

            authors = self._extract_authors_from_container(container)
            details = self._extract_publication_details(container)

            return Publication(
                title=title,
                authors=authors or [Author(name="[No authors]")],
                year=details.get("year"),
                journal=details.get("journal"),
                volume=details.get("volume"),
                issue=details.get("issue"),
                pages=details.get("pages"),
                doi=details.get("doi"),
                url=details.get("url"),
                abstract=details.get("abstract"),
                publication_type=details.get("type", "article"),
                source="Pure",
                raw_data=details,
            )

        except Exception as e:
            self.logger.error(f"Error parsing Pure publication container: {e}")
            return None

    def _extract_title_from_container(self, container: BeautifulSoup) -> Optional[str]:
        """Extract publication title."""
        # Try multiple title selectors
        title_selectors = [
            "h2",
            "h3",
            ".title",
            '[class*="title"]',
            'a[href*="publications"]',
        ]

        for selector in title_selectors:
            title_elem = container.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 10:  # Reasonable title length
                    return title

        return None

    def _extract_authors_from_container(self, container: BeautifulSoup) -> List[Author]:
        """Extract authors from publication container."""
        authors = []

        # Look for author information - check for individual name spans first
        name_elements = container.select(".persons .name, .persons span.name")
        if name_elements:
            for elem in name_elements:
                author_text = elem.get_text(strip=True)
                if author_text and not author_text.lower().startswith(("and", "&")):
                    authors.append(Author(name=author_text))
        else:
            # Fall back to broader selectors
            author_selectors = [".authors", '[class*="author"]', ".person-name", ".persons"]
            
            for selector in author_selectors:
                author_elements = container.select(selector)
                for elem in author_elements:
                    author_text = elem.get_text(strip=True)
                    if author_text:
                        # Simple author name splitting
                        author_names = [name.strip() for name in author_text.split(",")]
                        for name in author_names:
                            if name and not name.lower().startswith(("and", "&")):
                                authors.append(Author(name=name))
                if authors:  # Stop if we found authors
                    break

        return authors

    def _extract_publication_details(self, container: BeautifulSoup) -> Dict[str, Any]:
        """Extract publication details like journal, year, etc."""
        details = {}

        # Extract year from various patterns
        text = container.get_text()
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        if year_match:
            with contextlib.suppress(ValueError):
                details["year"] = int(year_match.group())

        # Look for journal/venue information
        venue_selectors = [
            ".journal",
            '[class*="journal"]',
            ".venue",
            '[class*="venue"]',
        ]
        for selector in venue_selectors:
            venue_elem = container.select_one(selector)
            if venue_elem:
                details["journal"] = venue_elem.get_text(strip=True)
                break

        # Look for DOI
        doi_links = container.find_all("a", href=re.compile(r"doi\.org|dx\.doi\.org"))
        if doi_links:
            doi_url = doi_links[0].get("href", "")
            doi_match = re.search(r"10\.\d+/[^\s]+", doi_url)
            if doi_match:
                details["doi"] = doi_match.group()

        # Look for full-text URL
        links = container.find_all("a", href=True)
        for link in links:
            href = link.get("href", "")
            if "publications" in href and href.startswith(("http", "/")):
                details["url"] = (
                    urljoin(self.base_domain, href) if href.startswith("/") else href
                )
                break

        return details

    def _parse_api_response(self, data: Dict[str, Any]) -> List[Publication]:
        """Parse Pure API response (implementation would be institution-specific)."""
        # This would need to be implemented based on the specific Pure API schema
        # Different institutions may have different API structures
        publications = []

        # Placeholder for API parsing logic
        # Pure API responses vary significantly between institutions
        self.logger.warning(
            "Pure API parsing not implemented - fell back to HTML scraping"
        )

        return publications
