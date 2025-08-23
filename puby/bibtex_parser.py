"""BibTeX parsing utilities for Zotero My Publications endpoint."""

import re
from typing import List, Optional

from .models import Author, Publication


class BibtexParser:
    """Parser for BibTeX entries from Zotero My Publications."""

    def __init__(self, logger=None):
        """Initialize parser with optional logger."""
        self.logger = logger

    def parse_bibtex_response(self, bibtex_content: str) -> List[Publication]:
        """Parse BibTeX response containing multiple entries."""
        publications = []

        # Split on @article, @book, etc.
        entries = re.split(r"@\w+\s*\{", bibtex_content)

        for entry in entries[1:]:  # Skip first empty split
            try:
                pub = self.parse_bibtex_entry(entry)
                if pub:
                    pub.source = "Zotero My Publications"
                    publications.append(pub)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Failed to parse BibTeX entry: {e}")
                continue

        return publications

    def parse_bibtex_entry(self, entry: str) -> Optional[Publication]:
        """Parse a single BibTeX entry into Publication."""
        try:
            # Extract title
            title_match = re.search(r"title\s*=\s*\{([^}]+)\}", entry, re.IGNORECASE)
            title = title_match.group(1) if title_match else ""

            if not title:
                return None

            # Extract and parse authors
            authors = self._parse_bibtex_authors(entry)
            if not authors:
                authors = [Author(name="[No authors]")]

            # Extract other fields
            year = self._extract_bibtex_year(entry)
            journal = self._extract_bibtex_field(entry, "journal")
            doi = self._extract_bibtex_field(entry, "doi")
            volume = self._extract_bibtex_field(entry, "volume")
            pages = self._extract_bibtex_field(entry, "pages")

            return Publication(
                title=title,
                authors=authors,
                year=year,
                journal=journal,
                doi=doi,
                volume=volume,
                pages=pages,
                source="Zotero My Publications",
                raw_data={"bibtex": entry},
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error parsing BibTeX entry: {e}")
            return None

    def _parse_bibtex_authors(self, entry: str) -> List[Author]:
        """Parse authors from BibTeX entry."""
        author_match = re.search(r"author\s*=\s*\{([^}]+)\}", entry, re.IGNORECASE)
        author_str = author_match.group(1) if author_match else ""

        authors = []
        if author_str:
            author_parts = author_str.split(" and ")
            for author_part in author_parts:
                author_part = author_part.strip()
                if "," in author_part:
                    parts = author_part.split(",", 1)
                    family_name = parts[0].strip()
                    given_name = parts[1].strip() if len(parts) > 1 else None
                    full_name = (
                        f"{given_name} {family_name}".strip()
                        if given_name
                        else family_name
                    )
                    authors.append(
                        Author(
                            name=full_name,
                            given_name=given_name,
                            family_name=family_name,
                        )
                    )
                else:
                    authors.append(Author(name=author_part))

        return authors

    def _extract_bibtex_year(self, entry: str) -> Optional[int]:
        """Extract year from BibTeX entry."""
        year_match = re.search(r"year\s*=\s*\{([^}]+)\}", entry, re.IGNORECASE)
        year_str = year_match.group(1) if year_match else ""

        if year_str:
            try:
                return int(year_str)
            except ValueError:
                pass
        return None

    def _extract_bibtex_field(self, entry: str, field_name: str) -> Optional[str]:
        """Extract a field value from BibTeX entry."""
        pattern = rf"{field_name}\s*=\s*\{{([^}}]+)\}}"
        match = re.search(pattern, entry, re.IGNORECASE)
        return match.group(1) if match else None
