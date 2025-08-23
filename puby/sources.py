"""Publication sources for fetching data."""

import logging
import random
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup, Tag
from pyzotero import zotero  # type: ignore

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
        title_info = title_data.get("title", {}) if title_data else {}
        return title_info.get("value", "") if title_info else ""

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
        if journal:
            value = journal.get("value", "")
            return value if value else None
        return None

    def _extract_doi(self, work: Dict[str, Any]) -> Optional[str]:
        """Extract DOI from ORCID work data."""
        external_ids = work.get("external-ids", {}).get("external-id", [])
        for ext_id in external_ids:
            if ext_id.get("external-id-type") == "doi":
                doi_value = ext_id.get("external-id-value")
                return str(doi_value) if doi_value else None
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
    """Fetch publications from Google Scholar profile via web scraping."""

    def __init__(self, scholar_url: str):
        """Initialize Scholar source."""
        self.scholar_url = scholar_url
        self.scholar_user_id = self._extract_scholar_id(scholar_url)
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://scholar.google.com/citations"

    def _extract_scholar_id(self, url: str) -> str:
        """Extract Scholar user ID from URL or return direct ID."""
        if not url:
            raise ValueError("Invalid Google Scholar URL or ID: empty string")

        # Check if it's already just a user ID (looks like Scholar ID pattern)
        # Scholar IDs are typically alphanumeric, may contain underscores/hyphens
        # but should not contain words like "invalid", "scholar", "url" etc.
        if (
            re.match(r"^[A-Za-z0-9_-]+$", url)
            and not url.startswith("http")
            and len(url) > 3
            and len(url) < 50
            and not any(
                word in url.lower() for word in ["invalid", "scholar", "url", "google"]
            )
        ):
            return url

        # Try to extract user ID from URL
        if "scholar.google.com" in url:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            user_id = query_params.get("user", [])
            if user_id:
                return user_id[0]

        raise ValueError(f"Invalid Google Scholar URL or ID: {url}")

    def _build_url(self, start: int) -> str:
        """Build Scholar profile URL with pagination."""
        return (
            f"{self.base_url}?user={self.scholar_user_id}&hl=en"
            f"&cstart={start}&pagesize=100"
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with proper User-Agent."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _apply_rate_limit(self) -> None:
        """Apply random delay to avoid being blocked."""
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
        class_attr = next_button.get("class")
        class_list = class_attr if isinstance(class_attr, list) else []
        return "disabled" not in class_list

    def _parse_publications_page(self, soup: BeautifulSoup) -> List[Publication]:
        """Parse publications from a single page."""
        publications: List[Publication] = []

        # Find publication table
        pub_table = soup.find("div", {"id": "gs_ccl"})
        if not pub_table:
            return publications

        # Find all publication rows
        pub_rows = pub_table.find_all("tr", class_="gsc_a_tr")
        if not isinstance(pub_rows, list):
            return publications

        for row in pub_rows:
            pub = self._parse_publication_row(row)
            if pub:
                publications.append(pub)

        return publications

    def _parse_publication_row(self, row: Union[Tag, Any]) -> Optional[Publication]:
        """Parse individual publication row."""
        try:
            title = self._extract_title_from_row(row)
            if not title:
                return None

            title_cell = row.find("td", class_="gsc_a_t")
            if not title_cell:
                return None

            authors, journal, year = self._extract_publication_metadata(title_cell)

            # Extract year from year column if not found in pub info
            if year is None:
                year = self._extract_year_from_column(row)

            return Publication(
                title=title,
                authors=authors,
                year=year,
                journal=journal,
                source="Google Scholar",
                raw_data={"html_row": str(row)},
            )

        except Exception as e:
            self.logger.error(f"Error parsing Scholar publication row: {e}")
            return None

    def _extract_title_from_row(self, row: Union[Tag, Any]) -> Optional[str]:
        """Extract title from publication row."""
        if not hasattr(row, 'find'):
            return None

        title_cell = row.find("td", class_="gsc_a_t")
        if not title_cell:
            return None

        title_link = title_cell.find("a", class_="gsc_a_at")
        if not title_link:
            return None

        title = title_link.get_text(strip=True)
        return title if title else None

    def _extract_publication_metadata(
        self, title_cell: Union[Tag, Any]
    ) -> Tuple[List[Author], Optional[str], Optional[int]]:
        """Extract authors, journal, and year from title cell."""
        if not hasattr(title_cell, 'find_all'):
            return [Author(name="[Authors not available]")], None, None

        gray_divs = title_cell.find_all("div", class_="gs_gray")
        if not isinstance(gray_divs, list):
            return [Author(name="[Authors not available]")], None, None

        authors: List[Author] = []
        journal: Optional[str] = None
        year: Optional[int] = None

        if len(gray_divs) >= 1:
            # First gray div typically contains authors
            authors = self._parse_authors(gray_divs[0].get_text(strip=True))
        else:
            # No author information available
            authors = [Author(name="[Authors not available]")]

        if len(gray_divs) >= 2:
            # Second gray div typically contains journal and year
            pub_info = gray_divs[1].get_text(strip=True)
            journal, year = self._parse_journal_and_year(pub_info)

        return authors, journal, year

    def _extract_year_from_column(self, row: Union[Tag, Any]) -> Optional[int]:
        """Extract year from the year column."""
        if not hasattr(row, 'find'):
            return None

        year_cell = row.find("td", class_="gsc_a_y")
        if not year_cell:
            return None

        year_span = year_cell.find("span", class_="gsc_a_h")
        if not year_span:
            return None

        year_text = year_span.get_text(strip=True)
        if not year_text:
            return None

        try:
            return int(year_text)
        except ValueError:
            return None

    def _parse_authors(self, author_text: str) -> List[Author]:
        """Parse authors from comma-separated text."""
        if not author_text.strip():
            return [Author(name="[Authors not available]")]

        authors = []
        for author in author_text.split(","):
            author_name = author.strip()
            if author_name:
                authors.append(Author(name=author_name))

        return authors if authors else [Author(name="[Authors not available]")]

    def _parse_journal_and_year(
        self, pub_info: str
    ) -> Tuple[Optional[str], Optional[int]]:
        """Parse journal name and year from publication info string."""
        if not pub_info.strip():
            return None, None

        # Handle special case: arXiv preprint with embedded year in identifier
        arxiv_match = re.search(r"arXiv:(\d{4})\.", pub_info)
        if arxiv_match:
            year = int(arxiv_match.group(1))
            # Remove the entire arXiv identifier for journal name
            journal = re.sub(r"\s*arXiv:[\d.]+.*$", "", pub_info).strip()
            return journal if journal else None, year

        # Try to extract year (4 consecutive digits at end, preceded by comma or space)
        year_match = re.search(r"[,\s]+((19|20)\d{2})$", pub_info)
        extracted_year: Optional[int] = int(year_match.group(1)) if year_match else None

        # If no year at end, try anywhere in the string
        if not extracted_year:
            year_match = re.search(r"\b(19|20)\d{2}\b", pub_info)
            extracted_year = int(year_match.group()) if year_match else None

        # Extract journal name
        journal = pub_info

        if year_match:
            # Everything before the year
            journal = pub_info[: year_match.start()].strip()

        # Clean up journal name by removing common patterns
        if journal:
            # Remove volume/issue/page info patterns like " 15 (4), 123-130" at end
            journal = re.sub(r"\s+\d+\s*\([^)]*\).*$", "", journal)
            # Remove trailing volume numbers like " 400, 109001"
            journal = re.sub(r"\s+\d+,.*$", "", journal)
            # Remove trailing commas and whitespace
            journal = re.sub(r"[,\s]+$", "", journal)
            journal = journal.strip()

        return journal if journal else None, extracted_year


class PureSource(PublicationSource):
    """Fetch publications from Pure research portal.
    
    Supports both HTML scraping and API access where available.
    Pure portals vary by institution but share common patterns.
    """

    def __init__(self, pure_url: str):
        """Initialize Pure source with validation."""
        if not pure_url or not pure_url.strip():
            raise ValueError("Invalid Pure portal URL: empty string")
        
        if not pure_url.startswith("http"):
            raise ValueError(f"Invalid Pure portal URL: {pure_url}")
            
        self.pure_url = pure_url.strip()
        self.logger = logging.getLogger(__name__)
        self._base_domain = self._extract_base_domain()

    def _extract_base_domain(self) -> str:
        """Extract base domain from Pure URL."""
        parsed = urlparse(self.pure_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _extract_person_id(self) -> str:
        """Extract person identifier from Pure URL."""
        # Pattern: /en/persons/person-identifier or /persons/person-identifier
        match = re.search(r"/persons/([^/?]+)", self.pure_url)
        if match:
            return match.group(1)
        raise ValueError(f"Cannot extract person ID from URL: {self.pure_url}")

    def _build_api_url(self) -> str:
        """Build Pure API URL for research outputs."""
        person_id = self._extract_person_id()
        return f"{self._base_domain}/ws/api/persons/{person_id}/research-outputs"

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with proper User-Agent."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _apply_rate_limit(self) -> None:
        """Apply delay to avoid overwhelming Pure portals."""
        delay = random.uniform(1.0, 2.0)
        time.sleep(delay)

    def fetch(self) -> List[Publication]:
        """Fetch publications from Pure portal.
        
        Attempts API access first, falls back to HTML scraping.
        """
        # Try API first if available
        try:
            api_url = self._build_api_url()
            self.logger.info(f"Attempting Pure API access: {api_url}")
            
            response = requests.get(api_url, headers={"Accept": "application/json"})
            if response.status_code == 200:
                return self._parse_api_response(response.json())
        except Exception as e:
            self.logger.debug(f"Pure API not available, falling back to HTML: {e}")

        # Fallback to HTML scraping
        return self._fetch_from_html()

    def _fetch_from_html(self) -> List[Publication]:
        """Fetch publications via HTML scraping with pagination support."""
        publications = []
        current_url = self.pure_url
        
        try:
            while current_url:
                self.logger.info(f"Fetching Pure page: {current_url}")
                
                response = requests.get(current_url, headers=self._get_headers())
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                page_publications = self._parse_html_page(soup)
                publications.extend(page_publications)
                
                # Check for next page
                next_url = self._find_next_page_url(soup)
                if next_url:
                    if not next_url.startswith("http"):
                        # Handle relative URLs - could be relative to current page or base domain
                        from urllib.parse import urljoin
                        next_url = urljoin(current_url, next_url)
                    current_url = next_url
                    self._apply_rate_limit()
                else:
                    break
                    
        except requests.RequestException as e:
            self.logger.error(f"Error fetching Pure data: {e}")
            
        return publications

    def _find_next_page_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Find URL for next page of results."""
        # Look for "Load more" or pagination links
        load_more = soup.find("div", class_="load-more")
        if load_more:
            link = load_more.find("a")
            if link and link.get("href"):
                return link["href"]
                
        # Look for pagination with page parameter
        pagination = soup.find("a", string=re.compile(r"next|more", re.I))
        if pagination and pagination.get("href"):
            return pagination["href"]
            
        return None

    def _parse_html_page(self, soup: BeautifulSoup) -> List[Publication]:
        """Parse publications from HTML page."""
        publications = []
        
        # Look for main content container
        content_div = soup.find("div", class_="result-container")
        if not content_div:
            return publications
            
        # Find publication containers  
        pub_containers = content_div.find_all("div", class_=re.compile(r"rendering.*contribution"))
        
        for container in pub_containers:
            pub = self._parse_publication_container(container)
            if pub:
                publications.append(pub)
                
        return publications

    def _parse_publication_container(self, container: BeautifulSoup) -> Optional[Publication]:
        """Parse individual publication container."""
        try:
            # Extract title
            title = self._extract_title_from_container(container)
            if not title:
                return None
                
            # Extract authors
            authors = self._extract_authors_from_container(container)
            
            # Extract publication details
            details = self._extract_publication_details(container)
            
            return Publication(
                title=title,
                authors=authors,
                year=details.get("year"),
                journal=details.get("journal"),
                volume=details.get("volume"),
                issue=details.get("issue"),
                pages=details.get("pages"),
                doi=details.get("doi"),
                url=details.get("url"),
                source="Pure",
                raw_data={"html": str(container)}
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing Pure publication: {e}")
            return None

    def _extract_title_from_container(self, container: BeautifulSoup) -> Optional[str]:
        """Extract publication title."""
        # Look for title in h3 or title class
        title_elem = container.find("h3", class_="title")
        if title_elem:
            link = title_elem.find("a")
            if link:
                title = link.get_text(strip=True)
                return title if title else None
                
        return None

    def _extract_authors_from_container(self, container: BeautifulSoup) -> List[Author]:
        """Extract authors from publication container."""
        authors = []
        
        # Look for persons/authors container
        persons_div = container.find("div", class_="persons")
        if persons_div:
            # Find author name spans
            name_spans = persons_div.find_all("span", class_="name")
            for span in name_spans:
                name = span.get_text(strip=True)
                if name and name not in [",", "and"]:
                    # Clean up name (remove trailing commas)
                    name = name.rstrip(",").strip()
                    if name:
                        authors.append(Author(name=name))
        
        return authors if authors else [Author(name="[Authors not available]")]

    def _extract_publication_details(self, container: BeautifulSoup) -> Dict[str, Any]:
        """Extract publication details like journal, year, etc."""
        details = {}
        
        details_div = container.find("div", class_="rendering_publicationdetails")
        if details_div:
            # Extract journal
            journal_span = details_div.find("span", class_="journal")
            if journal_span:
                details["journal"] = journal_span.get_text(strip=True)
                
            # Extract year
            date_span = details_div.find("span", class_="date")
            if date_span:
                year_text = date_span.get_text(strip=True)
                try:
                    details["year"] = int(year_text)
                except ValueError:
                    pass
                    
            # Extract volume, issue, pages
            volume_span = details_div.find("span", class_="volume")
            if volume_span:
                details["volume"] = volume_span.get_text(strip=True)
                
            issue_span = details_div.find("span", class_="issue")  
            if issue_span:
                details["issue"] = issue_span.get_text(strip=True)
                
            pages_span = details_div.find("span", class_="pages")
            if pages_span:
                details["pages"] = pages_span.get_text(strip=True)
                
        return details

    def _parse_api_response(self, data: Dict[str, Any]) -> List[Publication]:
        """Parse Pure API response (implementation would be institution-specific)."""
        # This is a placeholder for API parsing
        # Real implementation would need to handle institution-specific API formats
        self.logger.info("Pure API parsing not yet implemented for this portal")
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
                        "Please provide your numeric user ID in the group_id field. "
                        "You can find your user ID at: https://www.zotero.org/settings/keys"
                    )
                library_id = self.config.group_id

            self.zot = zotero.Zotero(
                library_id, self.config.library_type, self.config.api_key
            )
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
                # Don't silently return empty list - propagate the error
                raise ValueError(f"Failed to fetch Zotero data: {e}") from e

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
