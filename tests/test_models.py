"""Tests for publication models."""

from puby.models import Author, Publication, ZoteroConfig


class TestAuthor:
    """Test Author model."""

    def test_author_creation(self):
        """Test creating an author."""
        author = Author(
            name="John Doe",
            given_name="John",
            family_name="Doe",
            orcid="0000-0000-0000-0000",
        )
        assert author.name == "John Doe"
        assert author.given_name == "John"
        assert author.family_name == "Doe"
        assert author.orcid == "0000-0000-0000-0000"

    def test_author_str_with_full_name(self):
        """Test author string representation with full name."""
        author = Author(name="John Doe", given_name="John", family_name="Doe")
        assert str(author) == "Doe, John"

    def test_author_str_with_name_only(self):
        """Test author string representation with name only."""
        author = Author(name="John Doe")
        assert str(author) == "John Doe"


class TestPublication:
    """Test Publication model."""

    def test_publication_creation(self):
        """Test creating a publication."""
        authors = [Author(name="John Doe"), Author(name="Jane Smith")]
        pub = Publication(
            title="Test Publication",
            authors=authors,
            year=2023,
            doi="10.1234/test",
            journal="Test Journal",
        )
        assert pub.title == "Test Publication"
        assert len(pub.authors) == 2
        assert pub.year == 2023
        assert pub.doi == "10.1234/test"
        assert pub.journal == "Test Journal"

    def test_publication_str(self):
        """Test publication string representation."""
        authors = [Author(name="John Doe", family_name="Doe")]
        pub = Publication(
            title="Test Publication",
            authors=authors,
            year=2023,
            journal="Test Journal",
            doi="10.1234/test",
        )
        result = str(pub)
        assert "Doe" in result
        assert "2023" in result
        assert "Test Publication" in result
        assert "Test Journal" in result
        assert "10.1234/test" in result

    def test_publication_to_bibtex(self):
        """Test BibTeX generation."""
        authors = [
            Author(name="John Doe", family_name="Doe", given_name="John"),
            Author(name="Jane Smith", family_name="Smith", given_name="Jane"),
        ]
        pub = Publication(
            title="Test Publication",
            authors=authors,
            year=2023,
            journal="Test Journal",
            volume="10",
            issue="2",
            pages="100-110",
            doi="10.1234/test",
        )
        bibtex = pub.to_bibtex()
        assert "@article{Doe2023-100," in bibtex
        assert 'title = "{Test Publication}"' in bibtex
        assert 'author = "{Doe, John and Smith, Jane}"' in bibtex
        assert 'year = "{2023}"' in bibtex
        assert 'journal = "{Test Journal}"' in bibtex
        assert 'volume = "{10}"' in bibtex
        assert 'number = "{2}"' in bibtex
        assert 'pages = "{100-110}"' in bibtex
        assert 'doi = "{10.1234/test}"' in bibtex

    def test_publication_matches_by_doi(self):
        """Test publication matching by DOI."""
        pub1 = Publication(
            title="Test 1", authors=[Author(name="Author")], doi="10.1234/test"
        )
        pub2 = Publication(
            title="Test 2", authors=[Author(name="Different")], doi="10.1234/test"
        )
        pub3 = Publication(
            title="Test 3", authors=[Author(name="Another")], doi="10.5678/other"
        )

        assert pub1.matches(pub2)  # Same DOI
        assert not pub1.matches(pub3)  # Different DOI

    def test_publication_matches_by_title(self):
        """Test publication matching by title similarity."""
        pub1 = Publication(
            title="Machine Learning for Data Science",
            authors=[Author(name="Author")],
            year=2023,
        )
        pub2 = Publication(
            title="Machine Learning for Data Science",
            authors=[Author(name="Different")],
            year=2023,
        )
        pub3 = Publication(
            title="Completely Different Title",
            authors=[Author(name="Another")],
            year=2023,
        )

        assert pub1.matches(pub2, threshold=0.8)  # Same title
        assert not pub1.matches(pub3, threshold=0.8)  # Different title

    def test_calculate_similarity(self):
        """Test string similarity calculation."""
        pub = Publication(title="Test", authors=[])

        # Identical strings
        assert pub._calculate_similarity("hello world", "hello world") == 1.0

        # Completely different
        assert pub._calculate_similarity("hello world", "foo bar") == 0.0

        # Partial overlap
        similarity = pub._calculate_similarity("hello world test", "hello world")
        assert 0.5 <= similarity <= 1.0

        # Empty strings
        assert pub._calculate_similarity("", "") == 0.0
        assert pub._calculate_similarity("hello", "") == 0.0


class TestFuzzyTitleMatching:
    """Test fuzzy title matching functionality."""

    def test_normalize_title_basic(self):
        """Test basic title normalization."""
        pub = Publication(title="Test", authors=[])

        # Basic normalization
        assert pub._normalize_title("Hello World") == "hello world"
        assert pub._normalize_title("  Multiple   Spaces  ") == "multiple spaces"

    def test_normalize_title_latex_formatting(self):
        """Test LaTeX formatting removal."""
        pub = Publication(title="Test", authors=[])

        # LaTeX commands
        assert pub._normalize_title("\\textbf{Bold Text}") == "bold text"
        assert pub._normalize_title("\\textit{Italic Text}") == "italic text"
        assert pub._normalize_title("\\emph{Emphasized}") == "emphasized"
        assert pub._normalize_title("{Braced Text}") == "braced text"

        # Complex LaTeX
        title = "A Study of \\textbf{Machine Learning} in \\emph{Data Science}"
        expected = "a study of machine learning in data science"
        assert pub._normalize_title(title) == expected

    def test_normalize_title_html_entities(self):
        """Test HTML entity and tag removal."""
        pub = Publication(title="Test", authors=[])

        # HTML entities and tags
        assert (
            pub._normalize_title("Text&nbsp;with&amp;entities") == "text with entities"
        )
        assert pub._normalize_title("<b>Bold</b> <i>italic</i>") == "bold italic"

    def test_normalize_title_punctuation(self):
        """Test punctuation normalization."""
        pub = Publication(title="Test", authors=[])

        # Punctuation handling
        assert pub._normalize_title("Title: A Study!") == "title a study"
        assert pub._normalize_title("Multi-word hyphen") == "multi-word hyphen"
        assert pub._normalize_title("Question? Answer.") == "question answer"

    def test_fuzzy_similarity_jaccard(self):
        """Test basic Jaccard similarity calculation."""
        pub = Publication(title="Test", authors=[])

        # Identical normalized titles
        assert pub._calculate_fuzzy_similarity("hello world", "hello world") == 1.0

        # Complete overlap but different order
        sim = pub._calculate_fuzzy_similarity("world hello", "hello world")
        assert sim == 1.0

        # Partial overlap (gets boosted due to significant intersection)
        sim = pub._calculate_fuzzy_similarity("hello world test", "hello world")
        assert (
            sim > 2 / 3
        )  # 2 words in common, 3 total unique words, boosted for good overlap

        # No overlap
        assert pub._calculate_fuzzy_similarity("hello world", "foo bar") == 0.0

    def test_fuzzy_similarity_substring_matching(self):
        """Test substring matching for longer titles."""
        pub = Publication(title="Test", authors=[])

        # Long title containment (>15 chars)
        short = "machine learning algorithms"  # 26 chars
        long_title = "advanced machine learning algorithms for data science"

        sim = pub._calculate_fuzzy_similarity(short, long_title)
        # Should get high similarity due to containment
        assert sim > 0.7  # Should be high due to containment boost

    def test_matches_with_configurable_threshold(self):
        """Test matching with different threshold values."""
        pub1 = Publication(
            title="Machine Learning for Data Science",
            authors=[Author(name="Author")],
            year=2023,
        )
        pub2 = Publication(
            title="Machine Learning in Data Analysis",
            authors=[Author(name="Different")],
            year=2023,
        )

        # Should match with lower threshold
        assert pub1.matches(pub2, threshold=0.5)

        # Should not match with very high threshold
        assert not pub1.matches(pub2, threshold=0.9)

    def test_matches_with_year_consideration(self):
        """Test matching considering year information."""
        pub1 = Publication(
            title="Machine Learning Study",
            authors=[Author(name="Author")],
            year=2023,
        )
        pub2 = Publication(
            title="Machine Learning Study",
            authors=[Author(name="Different")],
            year=2022,  # Different year
        )
        pub3 = Publication(
            title="Machine Learning Study",
            authors=[Author(name="Another")],
            # No year
        )

        # Same title, different years should not match
        assert not pub1.matches(pub2, threshold=0.7)

        # Same title, one missing year should match (relies on title)
        assert pub1.matches(pub3, threshold=0.7)

    def test_matches_latex_title_variants(self):
        """Test matching with LaTeX formatting variations."""
        pub1 = Publication(
            title="Study of \\textbf{Machine Learning}",
            authors=[Author(name="Author")],
            year=2023,
        )
        pub2 = Publication(
            title="Study of Machine Learning",
            authors=[Author(name="Different")],
            year=2023,
        )

        # Should match despite LaTeX formatting differences
        assert pub1.matches(pub2, threshold=0.8)

    def test_matches_case_and_punctuation_variants(self):
        """Test matching with case and punctuation variations."""
        pub1 = Publication(
            title="Machine Learning: A Comprehensive Study!",
            authors=[Author(name="Author")],
            year=2023,
        )
        pub2 = Publication(
            title="machine learning a comprehensive study",
            authors=[Author(name="Different")],
            year=2023,
        )

        # Should match despite case and punctuation differences
        assert pub1.matches(pub2, threshold=0.8)

    def test_matches_substring_containment(self):
        """Test matching with title containment scenarios."""
        pub1 = Publication(
            title="Advanced Machine Learning Techniques",
            authors=[Author(name="Author")],
            year=2023,
        )
        pub2 = Publication(
            title="Advanced Machine Learning Techniques for Deep Neural Networks",
            authors=[Author(name="Different")],
            year=2023,
        )

        # Shorter title contained in longer should match
        assert pub1.matches(pub2, threshold=0.7)
        assert pub2.matches(pub1, threshold=0.7)  # Should be symmetric

    def test_matches_default_threshold(self):
        """Test that default threshold is 70%."""
        pub1 = Publication(
            title="Machine Learning Data Science",
            authors=[Author(name="Author")],
            year=2023,
        )
        pub2 = Publication(
            title="Machine Learning Analysis",
            authors=[Author(name="Different")],
            year=2023,
        )

        # Test default threshold (should be 0.7)
        # 2 words overlap out of 4 total = 50% - should not match with 70% default
        assert not pub1.matches(pub2)  # Uses default threshold=0.7

        # But should match with explicit lower threshold
        assert pub1.matches(pub2, threshold=0.4)


class TestZoteroConfig:
    """Test Zotero configuration model."""

    def test_zotero_config_creation(self):
        """Test creating Zotero configuration."""
        config = ZoteroConfig(
            api_key="abcdef1234567890abcdef12", group_id="12345", library_type="group"
        )
        assert config.api_key == "abcdef1234567890abcdef12"
        assert config.group_id == "12345"
        assert config.library_type == "group"

    def test_zotero_config_validation_valid(self):
        """Test valid Zotero configuration validation."""
        config = ZoteroConfig(
            api_key="P9NiFoyLeZu2bZNvvuQPDWsd", group_id="12345", library_type="group"
        )
        assert config.is_valid()
        assert len(config.validation_errors()) == 0

    def test_zotero_config_validation_invalid_api_key(self):
        """Test invalid API key validation."""
        config = ZoteroConfig(api_key="", group_id="12345", library_type="group")
        assert not config.is_valid()
        errors = config.validation_errors()
        assert any("API key is required" in error for error in errors)

    def test_zotero_config_validation_invalid_library_type(self):
        """Test invalid library type validation."""
        config = ZoteroConfig(
            api_key="validkey123456789abcdef01",
            group_id="12345",
            library_type="invalid",
        )
        assert not config.is_valid()
        errors = config.validation_errors()
        assert "Library type must be 'user' or 'group'" in errors

    def test_zotero_config_validation_user_type_with_user_id(self):
        """Test user library type validation with user ID."""
        config = ZoteroConfig(
            api_key="P9NiFoyLeZu2bZNvvuQPDWsd",
            group_id="12345",  # This is user_id for user libraries
            library_type="user",
        )
        assert config.is_valid()
        assert len(config.validation_errors()) == 0

    def test_zotero_config_validation_user_type_missing_user_id(self):
        """Test user library type validation without user ID."""
        # User ID is now optional for user libraries (will be auto-discovered from API key)
        config = ZoteroConfig(api_key="P9NiFoyLeZu2bZNvvuQPDWsd", library_type="user")
        assert config.is_valid()  # Now valid since we auto-discover user ID
        errors = config.validation_errors()
        assert len(errors) == 0  # No validation errors expected

    def test_zotero_config_validation_group_type_missing_group_id(self):
        """Test group library type validation without group ID."""
        config = ZoteroConfig(api_key="P9NiFoyLeZu2bZNvvuQPDWsd", library_type="group")
        assert not config.is_valid()
        errors = config.validation_errors()
        assert "Group ID is required for group library type" in errors



class TestPublicationValidation:
    """Test Publication validation methods."""

    def test_publication_validation_valid(self):
        """Test valid publication validation."""
        pub = Publication(title="Test Publication", authors=[Author(name="John Doe")])
        assert pub.is_valid()
        assert len(pub.validation_errors()) == 0

    def test_publication_validation_missing_title(self):
        """Test validation with missing title."""
        pub = Publication(title="", authors=[Author(name="John Doe")])
        assert not pub.is_valid()
        errors = pub.validation_errors()
        assert "Title is required" in errors

    def test_publication_validation_no_authors(self):
        """Test validation with no authors."""
        pub = Publication(title="Test Publication", authors=[])
        assert not pub.is_valid()
        errors = pub.validation_errors()
        assert "At least one author is required" in errors

    def test_publication_validation_invalid_doi_format(self):
        """Test validation with invalid DOI format."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Doe")],
            doi="invalid-doi",
        )
        assert not pub.is_valid()
        errors = pub.validation_errors()
        assert "DOI format is invalid" in errors

    def test_publication_validation_valid_doi_format(self):
        """Test validation with valid DOI format."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Doe")],
            doi="10.1234/test.doi",
        )
        assert pub.is_valid()
        assert len(pub.validation_errors()) == 0


class TestAuthorValidation:
    """Test Author validation methods."""

    def test_author_validation_valid(self):
        """Test valid author validation."""
        author = Author(name="John Doe")
        assert author.is_valid()
        assert len(author.validation_errors()) == 0

    def test_author_validation_missing_name(self):
        """Test validation with missing name."""
        author = Author(name="")
        assert not author.is_valid()
        errors = author.validation_errors()
        assert "Name is required" in errors

    def test_author_validation_invalid_orcid(self):
        """Test validation with invalid ORCID."""
        author = Author(name="John Doe", orcid="invalid-orcid")
        assert not author.is_valid()
        errors = author.validation_errors()
        assert "ORCID ID format is invalid" in errors


class TestCitationKeyGeneration:
    """Test citation key generation functionality."""

    def test_extract_first_author_surname_family_name(self):
        """Test extracting surname when family_name is available."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Doe", family_name="Doe", given_name="John")],
        )
        assert pub.extract_first_author_surname() == "Doe"

    def test_extract_first_author_surname_name_parsing_lastname_first(self):
        """Test extracting surname from 'Lastname, Firstname' format."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="Smith, John")],
        )
        assert pub.extract_first_author_surname() == "Smith"

    def test_extract_first_author_surname_name_parsing_firstname_last(self):
        """Test extracting surname from 'Firstname Lastname' format."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith")],
        )
        assert pub.extract_first_author_surname() == "Smith"

    def test_extract_first_author_surname_multiple_names(self):
        """Test extracting surname from complex names."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John van der Smith")],
        )
        assert pub.extract_first_author_surname() == "Smith"

    def test_extract_first_author_surname_special_characters(self):
        """Test extracting surname with special characters."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="José María García-López")],
        )
        assert pub.extract_first_author_surname() == "Garcia-Lopez"

    def test_extract_first_author_surname_no_authors(self):
        """Test extracting surname when no authors."""
        pub = Publication(
            title="Test Publication",
            authors=[],
        )
        assert pub.extract_first_author_surname() == "Unknown"

    def test_generate_citation_key_basic(self):
        """Test basic citation key generation."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            year=2023,
            pages="123-130",
        )
        assert pub.generate_citation_key() == "Smith2023-123"

    def test_generate_citation_key_no_pages(self):
        """Test citation key generation without pages."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            year=2023,
        )
        assert pub.generate_citation_key() == "Smith2023"

    def test_generate_citation_key_no_year(self):
        """Test citation key generation without year."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            pages="123-130",
        )
        assert pub.generate_citation_key() == "SmithNoYear-123"

    def test_generate_citation_key_no_year_no_pages(self):
        """Test citation key generation without year or pages."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
        )
        assert pub.generate_citation_key() == "SmithNoYear"

    def test_generate_citation_key_complex_pages(self):
        """Test citation key generation with complex page formats."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            year=2023,
            pages="e12345",
        )
        assert pub.generate_citation_key() == "Smith2023-e12345"

    def test_generate_citation_key_range_pages(self):
        """Test citation key generation with page ranges."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            year=2023,
            pages="123--130",
        )
        assert pub.generate_citation_key() == "Smith2023-123"

    def test_resolve_key_conflicts_no_conflict(self):
        """Test conflict resolution with no existing conflicts."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            year=2023,
            pages="123",
        )
        existing_keys = ["Other2023-456", "Different2024-123"]
        key = pub.resolve_key_conflicts(existing_keys)
        assert key == "Smith2023-123"

    def test_resolve_key_conflicts_single_conflict(self):
        """Test conflict resolution with one existing conflict."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            year=2023,
            pages="123",
        )
        existing_keys = ["Smith2023-123", "Other2023-456"]
        key = pub.resolve_key_conflicts(existing_keys)
        assert key == "Smith2023-123a"

    def test_resolve_key_conflicts_multiple_conflicts(self):
        """Test conflict resolution with multiple existing conflicts."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            year=2023,
            pages="123",
        )
        existing_keys = ["Smith2023-123", "Smith2023-123a", "Smith2023-123b"]
        key = pub.resolve_key_conflicts(existing_keys)
        assert key == "Smith2023-123c"

    def test_resolve_key_conflicts_no_pages(self):
        """Test conflict resolution without pages."""
        pub = Publication(
            title="Test Publication",
            authors=[Author(name="John Smith", family_name="Smith")],
            year=2023,
        )
        existing_keys = ["Smith2023", "Smith2023a"]
        key = pub.resolve_key_conflicts(existing_keys)
        assert key == "Smith2023b"
