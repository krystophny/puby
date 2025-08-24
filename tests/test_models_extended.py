"""Extended tests for models.py to achieve 80% coverage."""

import re
from datetime import date

from puby.models import Author, Publication, ZoteroConfig, _is_valid_orcid


class TestAuthorExtended:
    """Extended tests for Author model to improve coverage."""

    def test_author_validation_valid(self):
        """Test author validation with valid data."""
        author = Author(
            name="John Doe",
            given_name="John",
            family_name="Doe",
            orcid="0000-0000-0000-0000",
        )
        assert author.is_valid()
        assert author.validation_errors() == []

    def test_author_validation_empty_name(self):
        """Test author validation with empty name."""
        author = Author(name="")
        assert not author.is_valid()
        errors = author.validation_errors()
        assert "Name is required" in errors

    def test_author_validation_whitespace_name(self):
        """Test author validation with whitespace-only name."""
        author = Author(name="   ")
        assert not author.is_valid()
        errors = author.validation_errors()
        assert "Name is required" in errors

    def test_author_validation_invalid_orcid(self):
        """Test author validation with invalid ORCID."""
        author = Author(name="John Doe", orcid="invalid-orcid")
        assert not author.is_valid()
        errors = author.validation_errors()
        assert "ORCID ID format is invalid" in errors

    def test_author_validation_valid_orcid(self):
        """Test author validation with valid ORCID."""
        author = Author(name="John Doe", orcid="0000-0000-0000-0000")
        assert author.is_valid()
        assert author.validation_errors() == []

    def test_author_str_no_names(self):
        """Test author string representation with no given/family names."""
        author = Author(name="Full Name Only")
        assert str(author) == "Full Name Only"

    def test_author_str_partial_names(self):
        """Test author string representation with only family name."""
        author = Author(name="John Doe", family_name="Doe")
        # Without given_name, should fall back to full name
        assert str(author) == "John Doe"

    def test_author_affiliation(self):
        """Test author with affiliation."""
        author = Author(
            name="John Doe",
            given_name="John",
            family_name="Doe",
            affiliation="University of Example",
        )
        assert author.affiliation == "University of Example"


class TestPublicationExtended:
    """Extended tests for Publication model to improve coverage."""

    def test_publication_str_no_authors(self):
        """Test publication string representation with no authors."""
        pub = Publication(title="Test Publication", authors=[], year=2023)
        result = str(pub)
        assert "Test Publication" in result
        assert "(2023)" in result

    def test_publication_str_many_authors(self):
        """Test publication string representation with many authors (et al.)."""
        authors = [
            Author(name="Author 1"),
            Author(name="Author 2"),
            Author(name="Author 3"),
            Author(name="Author 4"),
            Author(name="Author 5"),
        ]
        pub = Publication(title="Test Publication", authors=authors, year=2023)
        result = str(pub)
        assert "et al." in result
        assert "Author 1" in result
        assert "Author 2" in result
        assert "Author 3" in result
        assert "Author 4" not in result  # Should not show 4th and 5th

    def test_publication_str_no_year(self):
        """Test publication string representation without year."""
        pub = Publication(title="Test Publication", authors=[Author(name="Author")])
        result = str(pub)
        assert "Test Publication" in result
        assert "Author" in result
        assert "(" not in result  # No year parentheses

    def test_publication_str_no_journal(self):
        """Test publication string representation without journal."""
        pub = Publication(
            title="Test Publication", authors=[Author(name="Author")], year=2023
        )
        result = str(pub)
        assert "Test Publication" in result
        # Should still have proper punctuation

    def test_publication_str_no_doi(self):
        """Test publication string representation without DOI."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="Author")],
            year=2023,
            journal="Test Journal",
        )
        result = str(pub)
        assert "Test Publication" in result
        assert "Test Journal" in result
        assert "DOI:" not in result

    def test_publication_bibtex_minimal(self):
        """Test BibTeX generation with minimal data."""
        pub = Publication(title="Test Title", authors=[Author(name="Test Author")])
        bibtex = pub.to_bibtex()
        assert "@article{" in bibtex
        assert "title = " in bibtex
        assert "Test Title" in bibtex

    def test_publication_bibtex_no_authors(self):
        """Test BibTeX generation with no authors."""
        pub = Publication(title="Test Title", authors=[], year=2023)
        bibtex = pub.to_bibtex()
        assert "title = " in bibtex
        assert "year = " in bibtex
        assert "author = " not in bibtex

    def test_publication_bibtex_complete(self):
        """Test BibTeX generation with complete data."""
        pub = Publication(
            title="Complete Test Publication",
            authors=[Author(name="John Doe"), Author(name="Jane Smith")],
            year=2023,
            journal="Test Journal",
            volume="10",
            issue="2",
            pages="100-110",
            doi="10.1234/test",
            url="https://example.com/article",
        )
        bibtex = pub.to_bibtex()
        assert "title = " in bibtex
        assert "author = " in bibtex
        assert "year = " in bibtex
        assert "journal = " in bibtex
        assert "volume = " in bibtex
        assert "number = " in bibtex
        assert "pages = " in bibtex
        assert "doi = " in bibtex
        assert "url = " in bibtex

    def test_publication_extract_first_author_surname_single_word(self):
        """Test extracting first author surname with single word name."""
        pub = Publication(
            title="Test", authors=[Author(name="Einstein", family_name="Einstein")]
        )
        surname = pub.extract_first_author_surname()
        assert surname == "Einstein"

    def test_publication_extract_first_author_surname_no_family_name(self):
        """Test extracting first author surname without family_name."""
        pub = Publication(title="Test", authors=[Author(name="John Doe")])
        surname = pub.extract_first_author_surname()
        assert surname == "Doe"  # Should extract last word as surname

    def test_publication_extract_first_author_surname_empty_name(self):
        """Test extracting first author surname with empty name."""
        pub = Publication(title="Test", authors=[Author(name="")])
        surname = pub.extract_first_author_surname()
        assert surname == "Unknown"

    def test_publication_extract_first_author_surname_no_authors(self):
        """Test extracting first author surname with no authors."""
        pub = Publication(title="Test", authors=[])
        surname = pub.extract_first_author_surname()
        assert surname == "Unknown"

    def test_publication_extract_first_page_simple(self):
        """Test extracting first page from simple range."""
        pub = Publication(title="Test", authors=[])
        assert pub._extract_first_page("123-130") == "123"
        assert pub._extract_first_page("100--200") == "100"
        assert pub._extract_first_page("50 to 60") == "50"

    def test_publication_extract_first_page_no_range(self):
        """Test extracting first page without range."""
        pub = Publication(title="Test", authors=[])
        assert pub._extract_first_page("123") == "123"
        assert pub._extract_first_page("e12345") == "e12345"

    def test_publication_extract_first_page_empty(self):
        """Test extracting first page from empty string."""
        pub = Publication(title="Test", authors=[])
        assert pub._extract_first_page("") == ""
        assert pub._extract_first_page(None) == ""

    def test_publication_generate_citation_key_with_page(self):
        """Test citation key generation with page number."""
        pub = Publication(
            title="Test",
            authors=[Author(name="John Doe", family_name="Doe")],
            year=2023,
            pages="100-110",
        )
        key = pub.generate_citation_key()
        assert key == "Doe2023-100"

    def test_publication_generate_citation_key_no_year(self):
        """Test citation key generation without year."""
        pub = Publication(
            title="Test",
            authors=[Author(name="John Doe", family_name="Doe")],
            pages="100-110",
        )
        key = pub.generate_citation_key()
        assert key == "DoeNoYear-100"

    def test_publication_generate_citation_key_no_pages(self):
        """Test citation key generation without pages."""
        pub = Publication(
            title="Test",
            authors=[Author(name="John Doe", family_name="Doe")],
            year=2023,
        )
        key = pub.generate_citation_key()
        assert key == "Doe2023"

    def test_publication_resolve_key_conflicts_no_conflict(self):
        """Test resolving citation key conflicts with no existing conflict."""
        pub = Publication(
            title="Test",
            authors=[Author(name="John Doe", family_name="Doe")],
            year=2023,
        )
        resolved = pub.resolve_key_conflicts(["Other2023", "Different2022"])
        assert resolved == "Doe2023"

    def test_publication_resolve_key_conflicts_with_conflict(self):
        """Test resolving citation key conflicts with existing conflict."""
        pub = Publication(
            title="Test",
            authors=[Author(name="John Doe", family_name="Doe")],
            year=2023,
        )
        resolved = pub.resolve_key_conflicts(["Doe2023", "Other2023"])
        assert resolved == "Doe2023a"

    def test_publication_resolve_key_conflicts_multiple_conflicts(self):
        """Test resolving citation key conflicts with multiple existing conflicts."""
        pub = Publication(
            title="Test",
            authors=[Author(name="John Doe", family_name="Doe")],
            year=2023,
        )
        resolved = pub.resolve_key_conflicts(["Doe2023", "Doe2023a", "Doe2023b"])
        assert resolved == "Doe2023c"

    def test_publication_matches_by_doi_case_insensitive(self):
        """Test publication matching by DOI with case differences."""
        pub1 = Publication(title="Test 1", authors=[], doi="10.1234/TEST")
        pub2 = Publication(title="Test 2", authors=[], doi="10.1234/test")
        assert pub1.matches(pub2)

    def test_publication_matches_by_title_exact_threshold(self):
        """Test publication matching by title at exact threshold."""
        pub1 = Publication(title="Test Publication Title", authors=[], year=2023)
        pub2 = Publication(title="Test Publication Title", authors=[], year=2023)
        assert pub1.matches(pub2, threshold=1.0)

    def test_publication_matches_by_title_different_years(self):
        """Test publication matching by title with different years."""
        pub1 = Publication(title="Same Title", authors=[], year=2023)
        pub2 = Publication(title="Same Title", authors=[], year=2022)
        # Should not match if both have years but they differ
        assert not pub1.matches(pub2, threshold=0.5)

    def test_publication_matches_by_title_missing_years(self):
        """Test publication matching by title with missing years."""
        pub1 = Publication(title="Same Title", authors=[])
        pub2 = Publication(title="Same Title", authors=[], year=2023)
        # Should match based on title similarity when one year is missing
        assert pub1.matches(pub2, threshold=0.9)

    def test_publication_matches_empty_titles(self):
        """Test publication matching with empty titles."""
        pub1 = Publication(title="", authors=[])
        pub2 = Publication(title="Something", authors=[])
        assert not pub1.matches(pub2)

    def test_publication_matches_no_titles(self):
        """Test publication matching with no titles."""
        pub1 = Publication(title=None, authors=[])
        pub2 = Publication(title="Something", authors=[])
        assert not pub1.matches(pub2)

    def test_publication_normalize_title(self):
        """Test title normalization."""
        pub = Publication(title="Test", authors=[])
        
        # Test various normalization cases
        assert pub._normalize_title("Simple Title") == "simple title"
        assert pub._normalize_title("Title: With Colon") == "title with colon"
        assert pub._normalize_title("Title (with parens)") == "title with parens"
        assert pub._normalize_title("Title, with; punctuation!") == "title with punctuation"

    def test_publication_normalize_title_accents(self):
        """Test title normalization with accented characters."""
        pub = Publication(title="Test", authors=[])
        normalized = pub._normalize_title("Café Résumé")
        assert "cafe" in normalized
        assert "resume" in normalized

    def test_publication_validation_valid(self):
        """Test publication validation with valid data."""
        pub = Publication(
            title="Valid Title",
            authors=[Author(name="Valid Author")],
            year=2023,
            doi="10.1234/valid",
        )
        assert pub.is_valid()
        assert pub.validation_errors() == []

    def test_publication_validation_empty_title(self):
        """Test publication validation with empty title."""
        pub = Publication(title="", authors=[])
        assert not pub.is_valid()
        errors = pub.validation_errors()
        assert "Title is required" in errors

    def test_publication_validation_invalid_year(self):
        """Test publication validation with invalid year."""
        pub = Publication(title="Test", authors=[], year=1800)
        assert not pub.is_valid()
        errors = pub.validation_errors()
        assert "Year must be between 1900 and" in str(errors)

    def test_publication_validation_future_year(self):
        """Test publication validation with future year."""
        pub = Publication(title="Test", authors=[], year=2050)
        assert not pub.is_valid()
        errors = pub.validation_errors()
        assert "Year must be between 1900 and" in str(errors)

    def test_publication_validation_invalid_authors(self):
        """Test publication validation with invalid authors."""
        invalid_author = Author(name="")  # Invalid author
        pub = Publication(title="Test", authors=[invalid_author])
        assert not pub.is_valid()
        errors = pub.validation_errors()
        assert any("Author 1" in error for error in errors)

    def test_publication_different_types(self):
        """Test publications with different types."""
        pub1 = Publication(title="Article", authors=[], publication_type="article")
        pub2 = Publication(title="Book", authors=[], publication_type="book")
        assert pub1.publication_type == "article"
        assert pub2.publication_type == "book"

    def test_publication_with_raw_data(self):
        """Test publication with raw data."""
        raw_data = {"source_id": "123", "api_version": "1.0"}
        pub = Publication(title="Test", authors=[], raw_data=raw_data)
        assert pub.raw_data["source_id"] == "123"
        assert pub.raw_data["api_version"] == "1.0"

    def test_publication_with_publication_date(self):
        """Test publication with publication date."""
        pub_date = date(2023, 6, 15)
        pub = Publication(title="Test", authors=[], publication_date=pub_date)
        assert pub.publication_date == pub_date

    def test_publication_fuzzy_similarity(self):
        """Test fuzzy similarity calculation."""
        pub = Publication(title="Test", authors=[])
        
        # Test identical strings
        similarity = pub._calculate_fuzzy_similarity("identical", "identical")
        assert similarity == 1.0
        
        # Test completely different strings
        similarity = pub._calculate_fuzzy_similarity("completely", "different")
        assert similarity < 0.5
        
        # Test similar strings
        similarity = pub._calculate_fuzzy_similarity("similar text", "similar test")
        assert 0.7 < similarity < 1.0


class TestZoteroConfigExtended:
    """Extended tests for ZoteroConfig model."""

    def test_zotero_config_creation(self):
        """Test creating ZoteroConfig with all parameters."""
        config = ZoteroConfig(
            api_key="test-key-123456789012345",
            group_id="12345",
            library_type="group",
            use_my_publications=False,
            format="json",
        )
        assert config.api_key == "test-key-123456789012345"
        assert config.group_id == "12345"
        assert config.library_type == "group"
        assert config.use_my_publications == False
        assert config.format == "json"

    def test_zotero_config_user_library(self):
        """Test ZoteroConfig for user library."""
        config = ZoteroConfig(
            api_key="test-key-123456789012345",
            group_id=None,
            library_type="user",
            use_my_publications=True,
            format="bibtex",
        )
        assert config.library_type == "user"
        assert config.group_id is None
        assert config.use_my_publications == True
        assert config.format == "bibtex"


class TestValidationFunctions:
    """Test validation functions."""

    def test_is_valid_orcid_valid(self):
        """Test ORCID validation with valid IDs."""
        assert _is_valid_orcid("0000-0000-0000-0000")
        assert _is_valid_orcid("0000-0001-2345-6789")
        assert _is_valid_orcid("0000-0002-1825-0097")

    def test_is_valid_orcid_invalid(self):
        """Test ORCID validation with invalid IDs."""
        assert not _is_valid_orcid("invalid")
        assert not _is_valid_orcid("0000-0000-0000")  # Too short
        assert not _is_valid_orcid("0000-0000-0000-000X")  # Invalid character
        assert not _is_valid_orcid("0000000000000000")  # No dashes
        assert not _is_valid_orcid("")
        assert not _is_valid_orcid(None)

    def test_is_valid_orcid_formatting(self):
        """Test ORCID validation with different formatting."""
        # Should handle various formats
        assert _is_valid_orcid("0000-0001-2345-6789")
        assert not _is_valid_orcid("0000 0001 2345 6789")  # Spaces instead of dashes