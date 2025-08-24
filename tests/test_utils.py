"""Tests for utility functions."""

import pytest

from puby.utils import (
    extract_year_from_bibtex_field,
    extract_year_from_text,
    safe_int_from_value,
)


class TestExtractYearFromText:
    """Test year extraction from generic text."""

    def test_extracts_valid_19xx_year(self):
        """Test extraction of years starting with 19."""
        assert extract_year_from_text("Published in 1995") == 1995
        assert extract_year_from_text("1900-2000") == 1900
        assert extract_year_from_text("Year: 1999") == 1999

    def test_extracts_valid_20xx_year(self):
        """Test extraction of years starting with 20."""
        assert extract_year_from_text("Published in 2023") == 2023
        assert extract_year_from_text("2001 was a good year") == 2001
        assert extract_year_from_text("Year: 2099") == 2099

    def test_extracts_first_valid_year(self):
        """Test that first valid year is extracted when multiple present."""
        assert extract_year_from_text("1995, 2023") == 1995
        assert extract_year_from_text("Published 2001, updated 2023") == 2001

    def test_ignores_invalid_years(self):
        """Test that invalid year formats are ignored."""
        assert extract_year_from_text("1800") is None  # Too old
        assert extract_year_from_text("2100") is None  # Too new
        assert extract_year_from_text("123") is None   # Too short
        assert extract_year_from_text("12345") is None # Too long

    def test_requires_word_boundaries(self):
        """Test that years must be word-bounded."""
        assert extract_year_from_text("ABC1995DEF") is None
        assert extract_year_from_text("1995") == 1995
        assert extract_year_from_text("(1995)") == 1995
        assert extract_year_from_text("1995.") == 1995

    def test_handles_empty_or_none_input(self):
        """Test handling of empty or None input."""
        assert extract_year_from_text("") is None
        assert extract_year_from_text(None) is None
        assert extract_year_from_text("   ") is None

    def test_handles_no_year_in_text(self):
        """Test when no valid year is present."""
        assert extract_year_from_text("No year here") is None
        assert extract_year_from_text("Some random text") is None


class TestExtractYearFromBibtexField:
    """Test year extraction from BibTeX entries."""

    def test_extracts_year_from_valid_bibtex(self):
        """Test extraction from valid BibTeX year field."""
        bibtex = "@article{key, year = {2023}, title = {Test}}"
        assert extract_year_from_bibtex_field(bibtex) == 2023

    def test_case_insensitive_field_matching(self):
        """Test that field matching is case insensitive."""
        bibtex = "@article{key, YEAR = {2023}, title = {Test}}"
        assert extract_year_from_bibtex_field(bibtex) == 2023
        
        bibtex = "@article{key, Year = {2023}, title = {Test}}"
        assert extract_year_from_bibtex_field(bibtex) == 2023

    def test_handles_whitespace_variations(self):
        """Test handling of various whitespace patterns."""
        bibtex = "@article{key,year={2023},title={Test}}"
        assert extract_year_from_bibtex_field(bibtex) == 2023
        
        bibtex = "@article{key, year   =   {2023}, title = {Test}}"
        assert extract_year_from_bibtex_field(bibtex) == 2023

    def test_extracts_first_year_field(self):
        """Test that first year field is used when multiple present."""
        bibtex = "@article{key, year = {2020}, year = {2023}}"
        assert extract_year_from_bibtex_field(bibtex) == 2020

    def test_handles_invalid_year_values(self):
        """Test handling of invalid year values."""
        bibtex = "@article{key, year = {not_a_year}}"
        assert extract_year_from_bibtex_field(bibtex) is None

    def test_handles_missing_year_field(self):
        """Test handling when year field is missing."""
        bibtex = "@article{key, title = {Test}}"
        assert extract_year_from_bibtex_field(bibtex) is None

    def test_handles_empty_or_none_input(self):
        """Test handling of empty or None input."""
        assert extract_year_from_bibtex_field("") is None
        assert extract_year_from_bibtex_field(None) is None

    def test_handles_year_with_extra_whitespace(self):
        """Test handling year values with extra whitespace."""
        bibtex = "@article{key, year = {  2023  }}"
        assert extract_year_from_bibtex_field(bibtex) == 2023


class TestSafeIntFromValue:
    """Test safe integer conversion utility."""

    def test_converts_valid_integers(self):
        """Test conversion of valid integer values."""
        assert safe_int_from_value(42) == 42
        assert safe_int_from_value(-10) == -10
        assert safe_int_from_value(0) == 0

    def test_converts_valid_strings(self):
        """Test conversion of valid string values."""
        assert safe_int_from_value("42") == 42
        assert safe_int_from_value("-10") == -10
        assert safe_int_from_value("0") == 0
        assert safe_int_from_value("  123  ") == 123

    def test_handles_invalid_strings(self):
        """Test handling of invalid string values."""
        assert safe_int_from_value("not_a_number") is None
        assert safe_int_from_value("12.5") is None
        assert safe_int_from_value("") is None
        assert safe_int_from_value("   ") is None

    def test_handles_none_input(self):
        """Test handling of None input."""
        assert safe_int_from_value(None) is None

    def test_handles_other_types(self):
        """Test handling of other types that can't be converted."""
        assert safe_int_from_value([]) is None
        assert safe_int_from_value({}) is None
        assert safe_int_from_value(12.5) == 12  # Float -> int conversion is allowed