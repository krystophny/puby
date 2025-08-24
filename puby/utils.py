"""Utility functions for common operations across sources."""

import re
from typing import Optional


def extract_year_from_text(text: str) -> Optional[int]:
    """Extract a 4-digit year from text using regex.
    
    Looks for 4-digit years in the range 1900-2099.
    
    Args:
        text: Text that may contain a year
        
    Returns:
        Extracted year as integer, or None if not found
    """
    if not text:
        return None
        
    # Match 4-digit years starting with 19 or 20
    year_match = re.search(r'\b(19|20)\d{2}\b', text.strip())
    if year_match:
        try:
            return int(year_match.group())
        except ValueError:
            pass
    return None


def extract_year_from_bibtex_field(entry: str) -> Optional[int]:
    """Extract year from BibTeX entry year field.
    
    Args:
        entry: BibTeX entry text
        
    Returns:
        Extracted year as integer, or None if not found
    """
    if not entry:
        return None
        
    year_match = re.search(r"year\s*=\s*\{([^}]+)\}", entry, re.IGNORECASE)
    year_str = year_match.group(1) if year_match else ""
    
    if year_str:
        try:
            return int(year_str.strip())
        except ValueError:
            pass
    return None


def safe_int_from_value(value) -> Optional[int]:
    """Safely convert a value to integer.
    
    Args:
        value: Value to convert (string, int, or other)
        
    Returns:
        Integer value, or None if conversion fails
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None