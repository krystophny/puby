"""Data models for publications."""

import re
import string
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

from .constants import (
    ZOTERO_API_KEY_REQUIRED_ERROR,
    ZOTERO_API_KEY_INVALID_FORMAT_ERROR,
)


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

        if self.orcid and not _is_valid_orcid(self.orcid):
            errors.append("ORCID ID format is invalid")

        return errors


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
        # Generate standardized citation key
        cite_key = self.generate_citation_key()

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

    def extract_first_author_surname(self) -> str:
        """Extract surname from first author for citation key generation."""
        if not self.authors:
            return "Unknown"

        author = self.authors[0]

        # Use family_name if available
        if author.family_name and author.family_name.strip():
            surname = author.family_name.strip()
        else:
            # Parse from name field
            surname = self._parse_surname_from_name(author.name)

        # Clean special characters and normalize
        return self._clean_surname_for_citation(surname)

    def _parse_surname_from_name(self, name: str) -> str:
        """Parse surname from various name formats."""
        if not name or not name.strip():
            return "Unknown"

        name = name.strip()

        # Format: "Lastname, Firstname"
        if "," in name:
            parts = name.split(",", 1)
            return parts[0].strip()

        # Format: "Firstname Lastname" or "Firstname Middle Lastname"
        # Take the last word as surname
        words = name.split()
        if words:
            return words[-1]

        return "Unknown"

    def _clean_surname_for_citation(self, surname: str) -> str:
        """Clean surname for citation key (remove accents, special chars)."""
        if not surname:
            return "Unknown"

        # Normalize unicode (decompose accents)
        surname = unicodedata.normalize("NFD", surname)

        # Remove combining characters (accents)
        surname = "".join(c for c in surname if unicodedata.category(c) != "Mn")

        # Replace non-ASCII letters and keep hyphens
        cleaned = ""
        for char in surname:
            if char.isascii() and (char.isalpha() or char == "-"):
                cleaned += char
            elif not char.isascii() and char.isalpha():
                # Try basic transliteration for common cases
                cleaned += self._transliterate_char(char)

        # Remove multiple consecutive hyphens and strip
        cleaned = re.sub(r"-+", "-", cleaned).strip("-")

        return cleaned if cleaned else "Unknown"

    def _transliterate_char(self, char: str) -> str:
        """Basic transliteration for non-ASCII characters."""
        # Simple mapping for common cases
        transliteration_map = {
            "ñ": "n",
            "ç": "c",
            "ß": "ss",
            "æ": "ae",
            "ø": "o",
            "å": "a",
            "ł": "l",
            "ż": "z",
            "ź": "z",
            "ś": "s",
        }
        return transliteration_map.get(char.lower(), char)

    def generate_citation_key(self) -> str:
        """Generate standardized citation key in AuthorYear-Page format."""
        surname = self.extract_first_author_surname()

        # Add year or "NoYear"
        year_str = str(self.year) if self.year else "NoYear"

        # Extract first page number if available
        page_part = ""
        if self.pages:
            page_part = self._extract_first_page(self.pages)
            if page_part:
                page_part = f"-{page_part}"

        return f"{surname}{year_str}{page_part}"

    def _extract_first_page(self, pages: str) -> str:
        """Extract first page number from pages string."""
        if not pages:
            return ""

        # Handle various page formats: "123-130", "123--130", "e12345", etc.
        pages = pages.strip()

        # Split on common separators
        for separator in ["-", "-", "—", " to ", " TO "]:
            if separator in pages:
                first_part = pages.split(separator)[0].strip()
                if first_part:
                    return first_part
                break

        # Return the whole string if no separators found
        return pages

    def resolve_key_conflicts(self, existing_keys: List[str]) -> str:
        """Resolve citation key conflicts by adding letter suffixes."""
        base_key = self.generate_citation_key()

        if base_key not in existing_keys:
            return base_key

        # Try adding letter suffixes: a, b, c, ...
        for letter in string.ascii_lowercase:
            candidate_key = f"{base_key}{letter}"
            if candidate_key not in existing_keys:
                return candidate_key

        # If we've exhausted single letters, something is very wrong
        # but return a fallback (this should never happen in practice)
        return f"{base_key}z"

    def matches(self, other: "Publication", threshold: float = 0.7) -> bool:
        """Check if this publication matches another based on fuzzy similarity.

        Args:
            other: Another publication to compare against
            threshold: Similarity threshold (0.0-1.0), default 70%

        Returns:
            bool: True if publications match based on similarity criteria
        """
        # Exact matching based on DOI (highest priority)
        if self.doi and other.doi:
            return self.doi.lower() == other.doi.lower()

        # Fuzzy matching based on title similarity and year
        if self.title and other.title:
            # Normalize titles for better comparison
            norm_title1 = self._normalize_title(self.title)
            norm_title2 = self._normalize_title(other.title)

            if not norm_title1 or not norm_title2:
                return False

            # Calculate title similarity with enhanced algorithm
            title_similarity = self._calculate_fuzzy_similarity(
                norm_title1, norm_title2
            )

            # Check year match (exact or both missing)
            year_match = (
                self.year == other.year
                if self.year and other.year
                else not (self.year or other.year)
            )

            # Enhanced matching: title similarity + optional year consideration
            base_match = title_similarity >= threshold
            if self.year and other.year:
                # If both have years, they should match
                return base_match and year_match
            else:
                # If one or both missing year, rely more on title similarity
                return base_match

        return False

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normalize title for fuzzy matching.

        Removes formatting, normalizes case and whitespace, handles LaTeX.

        Args:
            title: Raw title string

        Returns:
            str: Normalized title for comparison
        """
        if not title:
            return ""

        # Convert to lowercase
        normalized = title.lower()

        # Remove common LaTeX formatting
        latex_patterns = [
            (r"\\textbf\{([^}]+)\}", r"\1"),  # \textbf{text} -> text
            (r"\\textit\{([^}]+)\}", r"\1"),  # \textit{text} -> text
            (r"\\emph\{([^}]+)\}", r"\1"),  # \emph{text} -> text
            (r"\\text\{([^}]+)\}", r"\1"),  # \text{text} -> text
            (r"\\[a-zA-Z]+\{([^}]*)\}", r"\1"),  # Generic \command{text} -> text
            (r"\{([^}]+)\}", r"\1"),  # {text} -> text
            (r"\\[a-zA-Z]+", ""),  # Remove remaining LaTeX commands
        ]

        for pattern, replacement in latex_patterns:
            normalized = re.sub(pattern, replacement, normalized)

        # Remove HTML entities and tags
        html_patterns = [
            (r"&[a-zA-Z]+;", " "),  # &nbsp; etc.
            (r"<[^>]+>", " "),  # HTML tags
        ]

        for pattern, replacement in html_patterns:
            normalized = re.sub(pattern, replacement, normalized)

        # Normalize punctuation and whitespace
        normalized = re.sub(
            r"[^\w\s-]", " ", normalized
        )  # Keep letters, digits, spaces, hyphens
        normalized = re.sub(r"\s+", " ", normalized)  # Collapse multiple spaces
        normalized = normalized.strip()

        return normalized

    def _calculate_fuzzy_similarity(self, title1: str, title2: str) -> float:
        """Calculate enhanced fuzzy similarity between two normalized titles.

        Uses word overlap with substring matching for longer titles.

        Args:
            title1: First normalized title
            title2: Second normalized title

        Returns:
            float: Similarity score (0.0-1.0)
        """
        if not title1 or not title2:
            return 0.0

        # Split into words
        words1 = set(title1.split())
        words2 = set(title2.split())

        if not words1 or not words2:
            return 0.0

        # Calculate basic Jaccard similarity (word overlap)
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        jaccard_score = intersection / union if union > 0 else 0.0

        # Enhanced similarity for longer titles (>15 chars)
        # Check both substring containment and word-level containment
        if len(title1) > 15 or len(title2) > 15:
            # Method 1: Direct substring containment
            shorter, longer = (
                (title1, title2) if len(title1) <= len(title2) else (title2, title1)
            )

            if shorter in longer:
                # Very high similarity if one title contains the other
                containment_score = len(shorter) / len(longer)
                enhanced_containment = min(
                    1.0, containment_score + 0.2
                )  # Add flat bonus
                return max(jaccard_score, enhanced_containment)

            # Method 2: Check if all words from shorter title are in longer
            shorter_words, longer_words = (
                (words1, words2) if len(words1) <= len(words2) else (words2, words1)
            )

            if shorter_words.issubset(longer_words):
                # All words from shorter title are in longer title
                # Strong boost for perfect word subset cases
                word_containment_score = len(shorter_words) / len(longer_words)
                enhanced_score = min(
                    1.0, word_containment_score + 0.4
                )  # Add flat bonus
                return max(jaccard_score, enhanced_score)

        # For similar-length titles, boost Jaccard score if intersection is significant
        if intersection >= 2 and intersection / min(len(words1), len(words2)) >= 0.5:
            # Boost score when at least 2 words match and 50%+ of smaller set matches
            boost_factor = 1.2 if intersection >= 3 else 1.1
            return min(1.0, jaccard_score * boost_factor)

        return jaccard_score

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
    use_my_publications: bool = False
    format: str = "json"

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validation_errors()) == 0

    def validation_errors(self) -> List[str]:
        """Get list of validation errors."""
        errors = []

        if self.api_key is None or not self.api_key or not self.api_key.strip():
            errors.append(ZOTERO_API_KEY_REQUIRED_ERROR)
        elif not self._is_valid_api_key_format(self.api_key):
            errors.append(ZOTERO_API_KEY_INVALID_FORMAT_ERROR)

        if self.library_type not in ("user", "group"):
            errors.append("Library type must be 'user' or 'group'")

        if self.library_type == "group" and not self.group_id:
            errors.append("Group ID is required for group library type")

        if self.format not in ("json", "bibtex"):
            errors.append("Format must be 'json' or 'bibtex'")

        # User ID is now optional for user libraries (will be auto-discovered)
        # No validation error for missing user ID

        return errors

    @staticmethod
    def _is_valid_api_key_format(api_key: str) -> bool:
        """Validate Zotero API key format.

        Zotero API keys are exactly 24 characters long and contain only
        ASCII alphanumeric characters (letters and numbers, no special characters).

        Args:
            api_key: The API key to validate

        Returns:
            bool: True if the format is valid, False otherwise
        """
        if not api_key:
            return False

        # Must be exactly 24 characters
        if len(api_key) != 24:
            return False

        # Must contain only ASCII alphanumeric characters (letters and numbers)
        # Using all() with individual character checks for more precise control
        return all(c.isascii() and c.isalnum() for c in api_key)


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
        elif not _is_valid_orcid(self.orcid_id):
            errors.append("ORCID ID must follow format 0000-0000-0000-0000")

        return errors


def _is_valid_orcid(orcid: str) -> bool:
    """Validate ORCID ID format."""
    pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$"
    return bool(re.match(pattern, orcid))
