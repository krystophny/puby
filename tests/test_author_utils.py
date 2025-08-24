"""Tests for author parsing utilities."""

import pytest
from puby.author_utils import (
    parse_comma_separated_authors,
    parse_bibtex_authors,
    parse_plain_author_names,
    create_structured_author,
    create_fallback_author,
)
from puby.models import Author


class TestParseCommaSeparatedAuthors:
    """Test parsing authors from comma-separated text."""
    
    def test_basic_comma_separated(self):
        """Test basic comma-separated author parsing."""
        result = parse_comma_separated_authors("J Smith, M Johnson, K Lee")
        
        assert len(result) == 3
        assert result[0].name == "J Smith"
        assert result[1].name == "M Johnson"
        assert result[2].name == "K Lee"
    
    def test_empty_string(self):
        """Test empty string returns empty list."""
        result = parse_comma_separated_authors("")
        assert result == []
        
        result = parse_comma_separated_authors("   ")
        assert result == []
    
    def test_none_input(self):
        """Test None input returns empty list."""
        result = parse_comma_separated_authors(None)
        assert result == []
    
    def test_single_author(self):
        """Test single author (no commas)."""
        result = parse_comma_separated_authors("John Smith")
        
        assert len(result) == 1
        assert result[0].name == "John Smith"
        assert result[0].given_name == "John"
        assert result[0].family_name == "Smith"
    
    def test_filters_separator_words(self):
        """Test that separator words are filtered out."""
        result = parse_comma_separated_authors("J Smith, and, M Johnson, &, K Lee")
        
        assert len(result) == 3
        assert all(author.name not in ["and", "&"] for author in result)
    
    def test_handles_extra_whitespace(self):
        """Test handling of extra whitespace around names."""
        result = parse_comma_separated_authors("  J Smith  ,  M Johnson  ,  K Lee  ")
        
        assert len(result) == 3
        assert result[0].name == "J Smith"
        assert result[1].name == "M Johnson"
        assert result[2].name == "K Lee"


class TestParseBibtexAuthors:
    """Test parsing authors from BibTeX format."""
    
    def test_basic_bibtex_format(self):
        """Test basic BibTeX 'and' separated authors."""
        result = parse_bibtex_authors("Smith, John and Johnson, Mary and Lee, Kevin")
        
        assert len(result) == 3
        
        # Check first author
        assert result[0].name == "John Smith"
        assert result[0].given_name == "John"
        assert result[0].family_name == "Smith"
        
        # Check second author
        assert result[1].name == "Mary Johnson"
        assert result[1].given_name == "Mary"
        assert result[1].family_name == "Johnson"
    
    def test_bibtex_without_commas(self):
        """Test BibTeX format without commas (First Last)."""
        result = parse_bibtex_authors("John Smith and Mary Johnson")
        
        assert len(result) == 2
        assert result[0].name == "John Smith"
        assert result[0].given_name == "John"
        assert result[0].family_name == "Smith"
    
    def test_mixed_bibtex_formats(self):
        """Test mixed BibTeX formats in same string."""
        result = parse_bibtex_authors("Smith, John and Mary Johnson")
        
        assert len(result) == 2
        assert result[0].name == "John Smith"  # Last, First format
        assert result[1].name == "Mary Johnson"  # First Last format
    
    def test_empty_bibtex_string(self):
        """Test empty BibTeX string."""
        result = parse_bibtex_authors("")
        assert result == []
        
        result = parse_bibtex_authors("   ")
        assert result == []
    
    def test_single_bibtex_author(self):
        """Test single author in BibTeX format."""
        result = parse_bibtex_authors("Smith, John")
        
        assert len(result) == 1
        assert result[0].name == "John Smith"
        assert result[0].given_name == "John"
        assert result[0].family_name == "Smith"
    
    def test_bibtex_middle_names(self):
        """Test handling of middle names in BibTeX."""
        result = parse_bibtex_authors("Smith, John Michael and Johnson, Mary Ann")
        
        assert len(result) == 2
        assert result[0].name == "John Michael Smith"
        assert result[0].given_name == "John Michael"
        assert result[0].family_name == "Smith"


class TestParsePlainAuthorNames:
    """Test parsing authors from plain name lists."""
    
    def test_basic_name_list(self):
        """Test basic list of author names."""
        names = ["John Smith", "Mary Johnson", "Kevin Lee"]
        result = parse_plain_author_names(names)
        
        assert len(result) == 3
        assert result[0].name == "John Smith"
        assert result[1].name == "Mary Johnson" 
        assert result[2].name == "Kevin Lee"
    
    def test_empty_list(self):
        """Test empty list returns empty result."""
        result = parse_plain_author_names([])
        assert result == []
    
    def test_filters_empty_names(self):
        """Test that empty and whitespace-only names are filtered."""
        names = ["John Smith", "", "  ", "Mary Johnson", None]
        result = parse_plain_author_names(names)
        
        assert len(result) == 2
        assert result[0].name == "John Smith"
        assert result[1].name == "Mary Johnson"
    
    def test_filters_separator_words(self):
        """Test that separator words are filtered from name lists."""
        names = ["John Smith", "and", "Mary Johnson", "&", "Kevin Lee"]
        result = parse_plain_author_names(names)
        
        assert len(result) == 3
        assert all(author.name not in ["and", "&"] for author in result)
    
    def test_handles_whitespace(self):
        """Test handling of names with extra whitespace."""
        names = ["  John Smith  ", "  Mary Johnson  "]
        result = parse_plain_author_names(names)
        
        assert len(result) == 2
        assert result[0].name == "John Smith"
        assert result[1].name == "Mary Johnson"


class TestCreateStructuredAuthor:
    """Test creating authors from structured name components."""
    
    def test_both_names_provided(self):
        """Test creating author when both first and last names provided."""
        author = create_structured_author(
            first_name="John", 
            last_name="Smith"
        )
        
        assert author.name == "John Smith"
        assert author.given_name == "John"
        assert author.family_name == "Smith"
    
    def test_only_last_name(self):
        """Test creating author with only last name."""
        author = create_structured_author(last_name="Smith")
        
        assert author.name == "Smith"
        assert author.given_name is None
        assert author.family_name == "Smith"
    
    def test_only_first_name(self):
        """Test creating author with only first name."""
        author = create_structured_author(first_name="John")
        
        assert author.name == "John"
        assert author.given_name == "John"
        assert author.family_name is None
    
    def test_fallback_to_full_name(self):
        """Test fallback to full name when first/last not available."""
        author = create_structured_author(full_name="John Smith")
        
        assert author.name == "John Smith"
        assert author.given_name == "John"
        assert author.family_name == "Smith"
    
    def test_no_names_provided(self):
        """Test returns None when no names provided."""
        author = create_structured_author()
        assert author is None
        
        author = create_structured_author(first_name="", last_name="", full_name="")
        assert author is None
        
        author = create_structured_author(first_name="   ", last_name="   ")
        assert author is None
    
    def test_structured_names_take_precedence(self):
        """Test that structured names take precedence over full name."""
        author = create_structured_author(
            first_name="John",
            last_name="Smith", 
            full_name="Different Name"
        )
        
        # Should use structured names, not full name
        assert author.name == "John Smith"
        assert author.given_name == "John"
        assert author.family_name == "Smith"
    
    def test_handles_whitespace(self):
        """Test handling of whitespace in name components."""
        author = create_structured_author(
            first_name="  John  ",
            last_name="  Smith  "
        )
        
        assert author.name == "John Smith"
        assert author.given_name == "John"
        assert author.family_name == "Smith"


class TestCreateFallbackAuthor:
    """Test creating fallback authors."""
    
    def test_default_fallback(self):
        """Test creating fallback author with default text."""
        author = create_fallback_author()
        
        assert author.name == "[No authors]"
        assert author.given_name is None
        assert author.family_name is None
    
    def test_custom_fallback_text(self):
        """Test creating fallback author with custom text."""
        author = create_fallback_author("[Authors not available]")
        
        assert author.name == "[Authors not available]"
        assert author.given_name is None
        assert author.family_name is None


class TestNameParsing:
    """Test the internal name parsing logic."""
    
    def test_last_first_format(self):
        """Test parsing 'Last, First' format names via BibTeX parser.""" 
        # BibTeX parser is designed for "Last, First" format
        result = parse_bibtex_authors("Smith, John A")
        
        assert len(result) == 1
        author = result[0]
        assert author.name == "John A Smith"
        assert author.given_name == "John A"
        assert author.family_name == "Smith"
    
    def test_first_last_format(self):
        """Test parsing 'First Last' format names."""
        result = parse_plain_author_names(["John A Smith"])
        
        assert len(result) == 1
        author = result[0]
        assert author.name == "John A Smith"
        assert author.given_name == "John A"
        assert author.family_name == "Smith"
    
    def test_single_name(self):
        """Test handling of single word names."""
        result = parse_plain_author_names(["Smith"])
        
        assert len(result) == 1
        author = result[0]
        assert author.name == "Smith"
        assert author.given_name is None
        assert author.family_name == "Smith"
    
    def test_complex_names(self):
        """Test handling of complex name formats."""
        # Test hyphenated names
        result = parse_plain_author_names(["Mary Johnson-Smith"])
        assert result[0].family_name == "Johnson-Smith"
        
        # Test names with prefixes
        result = parse_plain_author_names(["John van der Berg"])
        assert result[0].given_name == "John van der"
        assert result[0].family_name == "Berg"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_very_long_names(self):
        """Test handling of very long names."""
        long_name = "John " + "Middle " * 10 + "Smith"
        result = parse_plain_author_names([long_name])
        
        assert len(result) == 1
        assert result[0].name == long_name
        assert result[0].family_name == "Smith"
    
    def test_special_characters(self):
        """Test handling of special characters in names."""
        names = ["João Silva", "François Müller", "李明"]
        result = parse_plain_author_names(names)
        
        assert len(result) == 3
        assert result[0].name == "João Silva"
        assert result[1].name == "François Müller"
        assert result[2].name == "李明"
    
    def test_numbers_in_names(self):
        """Test handling of numbers in names."""
        result = parse_plain_author_names(["John Smith Jr", "Mary Johnson II"])
        
        assert len(result) == 2
        assert result[0].name == "John Smith Jr"
        assert result[1].name == "Mary Johnson II"
    
    def test_many_separators(self):
        """Test handling of multiple consecutive separators."""
        result = parse_comma_separated_authors("Smith,,,Johnson")
        # Should handle gracefully, filtering empty parts
        assert all(author.name.strip() for author in result)
    
    def test_mixed_case_separator_words(self):
        """Test filtering separator words with different cases."""
        names = ["John Smith", "AND", "Mary Johnson", "&", "And", "Kevin Lee"]
        result = parse_plain_author_names(names)
        
        # Should filter all variations of separator words
        assert len(result) == 3
        assert all(author.name not in ["AND", "&", "And", "and"] for author in result)