"""Shared utilities for author parsing and handling."""

import re
from typing import List, Optional

from .models import Author


def parse_comma_separated_authors(author_text: str) -> List[Author]:
    """Parse authors from comma-separated text (e.g., Google Scholar format).
    
    Args:
        author_text: Comma-separated author string like "J Smith, M Johnson, K Lee"
        
    Returns:
        List of Author objects
    """
    authors = []
    if author_text and author_text.strip():
        # Split by comma and clean up
        author_names = [name.strip() for name in author_text.split(",")]
        for name in author_names:
            if name and not _is_separator_word(name):
                author = _create_author_from_name(name)
                if author:
                    authors.append(author)
    return authors


def parse_bibtex_authors(author_string: str) -> List[Author]:
    """Parse authors from BibTeX format author string.
    
    Args:
        author_string: BibTeX author string like "Last1, First1 and Last2, First2"
        
    Returns:
        List of Author objects with proper given/family name parsing
    """
    authors = []
    if author_string and author_string.strip():
        # Split by " and " (BibTeX standard)
        author_parts = author_string.split(" and ")
        for author_part in author_parts:
            author_part = author_part.strip()
            if author_part and not _is_separator_word(author_part):
                author = _parse_bibtex_name_format(author_part)
                if author:
                    authors.append(author)
    return authors


def parse_plain_author_names(names: List[str]) -> List[Author]:
    """Parse authors from a list of plain name strings.
    
    Args:
        names: List of author name strings
        
    Returns:
        List of Author objects
    """
    authors = []
    for name in names:
        if name and name.strip() and not _is_separator_word(name):
            author = _create_author_from_name(name.strip())
            if author:
                authors.append(author)
    return authors


def create_structured_author(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    full_name: Optional[str] = None
) -> Optional[Author]:
    """Create Author from structured name components (e.g., from Zotero API).
    
    Args:
        first_name: Given name (optional)
        last_name: Family name (optional)  
        full_name: Full name to use if first/last not available (optional)
        
    Returns:
        Author object or None if insufficient data
    """
    # Clean the inputs
    first_clean = first_name.strip() if first_name else ""
    last_clean = last_name.strip() if last_name else ""
    full_clean = full_name.strip() if full_name else ""
    
    # If we have both first and last names, use them
    if last_clean or first_clean:
        display_name = f"{first_clean} {last_clean}".strip()
        return Author(
            name=display_name,
            given_name=first_clean or None,
            family_name=last_clean or None,
        )
    
    # Fallback to full name if provided
    if full_clean:
        return _create_author_from_name(full_clean)
    
    return None


def create_fallback_author(fallback_text: str = "[No authors]") -> Author:
    """Create a fallback Author when no authors are found.
    
    Args:
        fallback_text: Text to use for the fallback author name
        
    Returns:
        Author object with the fallback text
    """
    return Author(name=fallback_text)


def _create_author_from_name(name: str) -> Optional[Author]:
    """Create Author object from a single name string, attempting to parse components.
    
    Args:
        name: Full name string in various formats
        
    Returns:
        Author object or None if name is invalid
    """
    name = name.strip()
    if not name:
        return None
    
    # Check for "Last, First" format
    if "," in name:
        return _parse_last_first_format(name)
    
    # Otherwise assume "First ... Last" format
    return _parse_first_last_format(name)


def _parse_last_first_format(name: str) -> Author:
    """Parse name in 'Last, First' format.
    
    Args:
        name: Name in format "Last, First Middle"
        
    Returns:
        Author object with parsed components
    """
    parts = name.split(",", 1)
    family_name = parts[0].strip()
    given_name = parts[1].strip() if len(parts) > 1 else ""
    
    # Reconstruct full name in natural order
    if given_name:
        full_name = f"{given_name} {family_name}".strip()
    else:
        full_name = family_name
    
    return Author(
        name=full_name,
        given_name=given_name or None,
        family_name=family_name or None,
    )


def _parse_first_last_format(name: str) -> Author:
    """Parse name in 'First Last' or 'First Middle Last' format.
    
    Args:
        name: Name in format "First Middle Last"
        
    Returns:
        Author object with parsed components
    """
    words = name.split()
    if not words:
        return Author(name=name)
    
    if len(words) == 1:
        # Single word - treat as family name
        return Author(name=name, family_name=name)
    
    # Multiple words - last is family, rest is given
    family_name = words[-1]
    given_name = " ".join(words[:-1])
    
    return Author(
        name=name,
        given_name=given_name,
        family_name=family_name,
    )


def _parse_bibtex_name_format(author_part: str) -> Optional[Author]:
    """Parse a single author from BibTeX format.
    
    Args:
        author_part: Single author string from BibTeX
        
    Returns:
        Author object or None if invalid
    """
    if not author_part.strip():
        return None
    
    # BibTeX format is typically "Last, First" or "First Last"
    if "," in author_part:
        return _parse_last_first_format(author_part)
    else:
        return _parse_first_last_format(author_part)


def _is_separator_word(text: str) -> bool:
    """Check if text is a separator word that should be ignored.
    
    Args:
        text: Text to check
        
    Returns:
        True if text is a separator word like "and", "&"
    """
    text_lower = text.lower().strip()
    return text_lower in ("and", "&", "et", "al", "et al", "et al.")