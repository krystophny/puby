"""Data models for publications."""

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional


@dataclass
class Author:
    """Represents a publication author."""

    name: str
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    orcid: Optional[str] = None
    affiliation: Optional[str] = None

    def __str__(self) -> str:
        """Return formatted author name."""
        if self.family_name and self.given_name:
            return f"{self.family_name}, {self.given_name}"
        return self.name

    def is_valid(self) -> bool:
        """Check if author data is valid."""
        return len(self.validation_errors()) == 0

    def validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        errors = []

        if not self.name or not self.name.strip():
            errors.append("Name is required")

        if self.orcid and not self._is_valid_orcid(self.orcid):
            errors.append("ORCID ID format is invalid")

        return errors

    @staticmethod
    def _is_valid_orcid(orcid: str) -> bool:
        """Validate ORCID ID format."""
        pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$"
        return bool(re.match(pattern, orcid))


@dataclass
class Publication:
    """Represents a scientific publication."""

    title: str
    authors: List[Author]
    year: Optional[int] = None
    doi: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    publication_date: Optional[date] = None
    publication_type: str = "article"
    source: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return formatted publication string."""
        author_str = ", ".join(str(a) for a in self.authors[:3])
        if len(self.authors) > 3:
            author_str += " et al."

        year_str = f" ({self.year})" if self.year else ""
        journal_str = f" {self.journal}" if self.journal else ""
        doi_str = f" DOI: {self.doi}" if self.doi else ""

        return f"{author_str}{year_str}. {self.title}.{journal_str}.{doi_str}"

    def to_bibtex(self) -> str:
        """Convert publication to BibTeX format."""
        # Generate a cite key
        first_author = self.authors[0].family_name if self.authors else "Unknown"
        year_str = str(self.year) if self.year else "NoYear"
        title_word = self.title.split()[0] if self.title else "NoTitle"
        cite_key = f"{first_author}{year_str}{title_word}"

        # Build BibTeX entry
        lines = [f"@article{{{cite_key},"]
        lines.append(f'  title = "{{{self.title}}}",')

        if self.authors:
            author_str = " and ".join(str(a) for a in self.authors)
            lines.append(f'  author = "{{{author_str}}}",')

        if self.year:
            lines.append(f'  year = "{{{self.year}}}",')

        if self.journal:
            lines.append(f'  journal = "{{{self.journal}}}",')

        if self.volume:
            lines.append(f'  volume = "{{{self.volume}}}",')

        if self.issue:
            lines.append(f'  number = "{{{self.issue}}}",')

        if self.pages:
            lines.append(f'  pages = "{{{self.pages}}}",')

        if self.doi:
            lines.append(f'  doi = "{{{self.doi}}}",')

        if self.url:
            lines.append(f'  url = "{{{self.url}}}",')

        lines.append("}")

        return "\n".join(lines)

    def matches(self, other: "Publication", threshold: float = 0.8) -> bool:
        """Check if this publication matches another based on similarity."""
        # Simple matching based on DOI
        if self.doi and other.doi:
            return self.doi.lower() == other.doi.lower()

        # Match based on title similarity and year
        if self.title and other.title:
            title_similarity = self._calculate_similarity(
                self.title.lower(), other.title.lower()
            )
            year_match = self.year == other.year if self.year and other.year else True

            return title_similarity >= threshold and year_match

        return False

    @staticmethod
    def _calculate_similarity(s1: str, s2: str) -> float:
        """Calculate simple similarity between two strings."""
        # Simple character-based similarity
        if not s1 or not s2:
            return 0.0

        # Normalize strings
        s1_words = set(s1.lower().split())
        s2_words = set(s2.lower().split())

        if not s1_words or not s2_words:
            return 0.0

        # Jaccard similarity
        intersection = len(s1_words & s2_words)
        union = len(s1_words | s2_words)

        return intersection / union if union > 0 else 0.0

    def is_valid(self) -> bool:
        """Check if publication data is valid."""
        return len(self.validation_errors()) == 0

    def validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        errors = []

        if not self.title or not self.title.strip():
            errors.append("Title is required")

        if not self.authors:
            errors.append("At least one author is required")

        if self.doi and not self._is_valid_doi(self.doi):
            errors.append("DOI format is invalid")

        return errors

    @staticmethod
    def _is_valid_doi(doi: str) -> bool:
        """Validate DOI format."""
        pattern = r"^10\.\d+/.+"
        return bool(re.match(pattern, doi))


@dataclass
class ZoteroConfig:
    """Configuration for Zotero API access."""

    api_key: str
    group_id: Optional[str] = None
    library_type: str = "user"

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validation_errors()) == 0

    def validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        errors = []

        if not self.api_key or not self.api_key.strip():
            errors.append("API key is required")

        if self.library_type not in ("user", "group"):
            errors.append("Library type must be 'user' or 'group'")

        if self.library_type == "group" and not self.group_id:
            errors.append("Group ID is required for group library type")

        if self.library_type == "user" and not self.group_id:
            errors.append("User ID is required for user library type")

        return errors


@dataclass
class ORCIDConfig:
    """Configuration for ORCID API access."""

    orcid_id: str

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validation_errors()) == 0

    def validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        errors = []

        if not self.orcid_id or not self.orcid_id.strip():
            errors.append("ORCID ID is required")
        elif not self._is_valid_orcid(self.orcid_id):
            errors.append("ORCID ID must follow format 0000-0000-0000-0000")

        return errors

    @staticmethod
    def _is_valid_orcid(orcid: str) -> bool:
        """Validate ORCID ID format."""
        pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$"
        return bool(re.match(pattern, orcid))
