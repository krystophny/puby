"""Tests for publication models."""

import pytest
from datetime import date

from puby.models import Author, Publication


class TestAuthor:
    """Test Author model."""
    
    def test_author_creation(self):
        """Test creating an author."""
        author = Author(
            name="John Doe",
            given_name="John",
            family_name="Doe",
            orcid="0000-0000-0000-0000"
        )
        assert author.name == "John Doe"
        assert author.given_name == "John"
        assert author.family_name == "Doe"
        assert author.orcid == "0000-0000-0000-0000"
    
    def test_author_str_with_full_name(self):
        """Test author string representation with full name."""
        author = Author(
            name="John Doe",
            given_name="John",
            family_name="Doe"
        )
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
            journal="Test Journal"
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
            doi="10.1234/test"
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
            Author(name="Jane Smith", family_name="Smith", given_name="Jane")
        ]
        pub = Publication(
            title="Test Publication",
            authors=authors,
            year=2023,
            journal="Test Journal",
            volume="10",
            issue="2",
            pages="100-110",
            doi="10.1234/test"
        )
        bibtex = pub.to_bibtex()
        assert "@article{Doe2023Test," in bibtex
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
            title="Test 1",
            authors=[Author(name="Author")],
            doi="10.1234/test"
        )
        pub2 = Publication(
            title="Test 2",
            authors=[Author(name="Different")],
            doi="10.1234/test"
        )
        pub3 = Publication(
            title="Test 3",
            authors=[Author(name="Another")],
            doi="10.5678/other"
        )
        
        assert pub1.matches(pub2)  # Same DOI
        assert not pub1.matches(pub3)  # Different DOI
    
    def test_publication_matches_by_title(self):
        """Test publication matching by title similarity."""
        pub1 = Publication(
            title="Machine Learning for Data Science",
            authors=[Author(name="Author")],
            year=2023
        )
        pub2 = Publication(
            title="Machine Learning for Data Science",
            authors=[Author(name="Different")],
            year=2023
        )
        pub3 = Publication(
            title="Completely Different Title",
            authors=[Author(name="Another")],
            year=2023
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