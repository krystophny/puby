"""Zotero publication source implementation."""

import logging
import re
from typing import Any, Dict, List, Optional

import requests
from pyzotero import zotero  # type: ignore

from .base import PublicationSource
from .bibtex_parser import BibtexParser
from .constants import ZOTERO_API_KEY_URL, ZOTERO_API_KEY_INVALID_ERROR
from .models import Author, Publication, ZoteroConfig
from .author_utils import create_structured_author, create_fallback_author
from .http_utils import get_session_for_url


class ZoteroSource(PublicationSource):
    """Modern Zotero API client using ZoteroConfig."""

    def __init__(self, config: ZoteroConfig):
        """Initialize Zotero source with configuration."""
        if not config.is_valid():
            errors = ", ".join(config.validation_errors())
            raise ValueError(f"Invalid Zotero configuration: {errors}")

        self.config = config
        self.logger = logging.getLogger(__name__)
        self._session = get_session_for_url("https://api.zotero.org")

        # Initialize Zotero API client
        try:
            if self.config.library_type == "group":
                if not self.config.group_id:
                    raise ValueError("Group ID required for group library type")
                library_id = self.config.group_id
            else:
                # For user libraries, auto-discover user ID if not provided
                if not self.config.group_id:
                    library_id = self._autodiscover_user_id(self.config.api_key)
                    self.logger.info(f"Auto-discovered user ID: {library_id}")
                else:
                    library_id = self.config.group_id

            self.zot = zotero.Zotero(
                library_id, self.config.library_type, self.config.api_key
            )

            # Validate connection during initialization
            self.validate_connection()

        except Exception as e:
            # Provide helpful guidance for common authentication issues
            error_msg = str(e).lower()
            if any(
                term in error_msg
                for term in ["api key", "auth", "credentials", "unauthorized"]
            ):
                raise ValueError(
                    f"Failed to initialize Zotero client: {e}. "
                    f"Please ensure you have a valid API key. "
                    f"Get your API key at: {ZOTERO_API_KEY_URL}"
                ) from e
            else:
                raise ValueError(f"Failed to initialize Zotero client: {e}") from e

    def validate_connection(self) -> None:
        """Validate the connection to Zotero API.

        Raises:
            ValueError: If connection validation fails with specific error message.
        """
        try:
            # Test connection by fetching collections (lightweight operation)
            self.zot.collections()
            self.logger.info("Zotero connection validated successfully")
        except Exception as e:
            error_msg = str(e).lower()

            if any(
                term in error_msg
                for term in ["403", "forbidden", "unauthorized", "auth"]
            ):
                raise ValueError(
                    "Zotero authentication failed: Invalid API key or insufficient permissions. "
                    f"Please check your API key at: {ZOTERO_API_KEY_URL}"
                ) from e
            elif any(term in error_msg for term in ["404", "not found"]):
                raise ValueError(
                    f"Zotero library not found: The specified library ID '{self.config.group_id}' "
                    f"does not exist or you don't have access to it."
                ) from e
            elif any(
                term in error_msg
                for term in ["network", "connection", "timeout", "unreachable"]
            ):
                raise ValueError(
                    "Zotero connection failed: Network error. "
                    "Please check your internet connection and try again."
                ) from e
            else:
                raise ValueError(f"Zotero connection validation failed: {e}") from e

    def _autodiscover_user_id(self, api_key: str) -> str:
        """Auto-discover user ID from API key using Zotero API."""
        url = "https://api.zotero.org/keys/current"
        headers = {"Zotero-API-Key": api_key, "Accept": "application/json"}

        try:
            response = self._session.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Extract user ID from response
            user_id = data.get("userID")
            if not user_id:
                raise ValueError(
                    "Invalid response from Zotero API: missing userID field. "
                    "Please verify your API key is valid."
                )

            return str(user_id)

        except requests.HTTPError as e:
            if hasattr(e, "response") and e.response and e.response.status_code == 403:
                raise ValueError(
                    "Failed to auto-discover user ID: Invalid API key. "
                    f"Please verify your API key at: {ZOTERO_API_KEY_URL}"
                ) from e
            else:
                status_code = (
                    e.response.status_code
                    if hasattr(e, "response") and e.response
                    else "unknown"
                )
                raise ValueError(
                    f"Failed to auto-discover user ID: HTTP {status_code} error. "
                    f"Please check your API key or provide user ID manually."
                ) from e
        except requests.ConnectionError as e:
            raise ValueError(
                "Failed to auto-discover user ID: Network error. "
                "Please check your internet connection or provide user ID manually."
            ) from e
        except Exception as e:
            raise ValueError(
                f"Failed to auto-discover user ID: {e}. "
                f"Please provide user ID manually or check your API key."
            ) from e

    def fetch(self) -> List[Publication]:
        """Fetch publications from Zotero library with pagination support."""
        # Try My Publications endpoint if enabled for user libraries
        if self.config.use_my_publications and self.config.library_type == "user":
            try:
                return self._fetch_my_publications()
            except Exception as e:
                error_msg = str(e).lower()
                # If My Publications endpoint fails, fall back to regular library
                if "404" in error_msg or "not found" in error_msg:
                    self.logger.info(
                        "My Publications endpoint not available, falling back to regular library"
                    )
                else:
                    # Re-raise other errors (auth, network, etc.)
                    raise

        # Regular library fetch
        return self._fetch_library_items()

    def _fetch_library_items(self) -> List[Publication]:
        """Fetch publications from regular Zotero library."""
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

            if any(
                term in error_msg
                for term in [
                    "auth",
                    "unauthorized",
                    "forbidden",
                    "api key",
                    "credentials",
                ]
            ):
                self.logger.error(
                    f"Zotero authentication failed: {e}. "
                    f"Please check your API key is valid. "
                    f"Get your API key at: {ZOTERO_API_KEY_URL}"
                )
                raise ValueError(
                    "Zotero API authentication failed. Please provide a valid API key. "
                    f"Get your API key at: {ZOTERO_API_KEY_URL}"
                ) from e
            elif any(
                term in error_msg
                for term in ["network", "connection", "timeout", "unreachable"]
            ):
                self.logger.error(f"Zotero network connection failed: {e}")
                raise ValueError(
                    "Zotero connection failed: Network error. "
                    "Please check your internet connection and try again."
                ) from e
            else:
                self.logger.error(f"Error fetching Zotero data: {e}")
                # Don't silently return empty list - propagate the error
                raise ValueError(f"Failed to fetch Zotero data: {e}") from e

        self.logger.info(f"Parsed {len(publications)} publications from Zotero")
        return publications

    def _fetch_my_publications(self) -> List[Publication]:
        """Fetch publications from Zotero My Publications endpoint."""
        user_id = self._get_my_publications_user_id()
        self.logger.info(f"Fetching from My Publications endpoint for user {user_id}")

        publications = []
        start = 0
        limit = 100

        try:
            while True:
                page_pubs = self._fetch_my_publications_page(user_id, start, limit)
                if not page_pubs:
                    break

                publications.extend(page_pubs)

                # Handle pagination
                if self.config.format == "bibtex" or len(page_pubs) < limit:
                    break
                start += limit

        except Exception as e:
            self._handle_my_publications_error(e)

        self.logger.info(
            f"Parsed {len(publications)} publications from My Publications"
        )
        return publications

    def _get_my_publications_user_id(self) -> str:
        """Get user ID for My Publications endpoint."""
        if self.config.library_type != "user":
            raise ValueError(
                "My Publications endpoint is only available for user libraries"
            )

        user_id = self.config.group_id
        if not user_id:
            user_id = self._autodiscover_user_id(self.config.api_key)

        return user_id

    def _fetch_my_publications_page(
        self, user_id: str, start: int, limit: int
    ) -> List[Publication]:
        """Fetch a single page of My Publications."""
        url = f"https://api.zotero.org/users/{user_id}/publications/items"
        headers, params = self._build_my_publications_request(start, limit)

        response = self._session.get(url, headers=headers, params=params)
        self._validate_my_publications_response(response)

        return self._parse_my_publications_response(response)

    def _build_my_publications_request(self, start: int, limit: int) -> tuple:
        """Build request headers and parameters for My Publications."""
        if self.config.format == "bibtex":
            headers = {
                "Zotero-API-Key": self.config.api_key,
                "Accept": "application/x-bibtex",
            }
            params = {"format": "bibtex", "limit": limit, "start": start}
        else:
            headers = {
                "Zotero-API-Key": self.config.api_key,
                "Accept": "application/json",
            }
            params = {"format": "json", "limit": limit, "start": start}

        return headers, params

    def _validate_my_publications_response(self, response) -> None:
        """Validate My Publications API response."""
        if response.status_code == 403:
            raise ValueError(
                "Zotero My Publications authentication failed: Invalid API key. "
                f"Please check your API key at: {ZOTERO_API_KEY_URL}"
            )
        elif response.status_code == 404:
            raise ValueError("My Publications endpoint not found")
        elif response.status_code != 200:
            response.raise_for_status()

    def _parse_my_publications_response(self, response) -> List[Publication]:
        """Parse My Publications API response."""
        if self.config.format == "bibtex":
            parser = BibtexParser(self.logger)
            return parser.parse_bibtex_response(response.text)
        else:
            items = response.json()
            publications = []
            for item in items:
                pub = self._parse_zotero_item(item)
                if pub:
                    pub.source = "Zotero My Publications"
                    publications.append(pub)
            return publications

    def _handle_my_publications_error(self, error: Exception) -> None:
        """Handle errors from My Publications endpoint."""
        if isinstance(error, requests.ConnectionError):
            raise ValueError(
                "Zotero My Publications connection failed: Network error. "
                "Please check your internet connection."
            ) from error
        elif isinstance(error, requests.HTTPError):
            error_msg = str(error).lower()
            if "403" in error_msg or "forbidden" in error_msg:
                raise ValueError(
                    "Zotero My Publications authentication failed: Invalid API key. "
                    f"Please check your API key at: {ZOTERO_API_KEY_URL}"
                ) from error
            else:
                raise ValueError(f"Failed to fetch My Publications: {error}") from error
        else:
            raise ValueError(f"Failed to fetch My Publications: {error}") from error

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
        """Extract and parse authors from Zotero creators data using shared utilities."""
        authors = []
        creators = data.get("creators", [])
        for creator in creators:
            if creator.get("creatorType") == "author":
                first_name = creator.get("firstName", "").strip()
                last_name = creator.get("lastName", "").strip()
                
                # Use shared utility to create structured author
                author = create_structured_author(
                    first_name=first_name or None,
                    last_name=last_name or None
                )
                if author:
                    authors.append(author)

        return authors if authors else [create_fallback_author("[No authors]")]

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