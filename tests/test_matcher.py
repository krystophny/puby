"""Tests for publication matching and comparison utilities."""

import pytest
from datetime import date

from puby.models import Author, Publication
from puby.matcher import PublicationMatcher, MatchResult


@pytest.fixture
def sample_publications():
    """Create sample publications for testing."""
    pub1 = Publication(
        title="Machine Learning in Scientific Computing",
        authors=[
            Author("Smith, John", given_name="John", family_name="Smith"),
            Author("Doe, Jane", given_name="Jane", family_name="Doe"),
        ],
        year=2023,
        doi="10.1000/example.2023.001",
        journal="Journal of Science",
        source="orcid",
    )

    pub2 = Publication(
        title="machine learning in scientific computing",  # lowercase variation
        authors=[
            Author("Smith, J.", given_name="J.", family_name="Smith"),
            Author("Doe, J.", given_name="J.", family_name="Doe"),
        ],
        year=2023,
        doi="10.1000/example.2023.001",  # same DOI
        journal="Journal of Science",
        source="zotero",
    )

    pub3 = Publication(
        title="Deep Learning Applications in Physics",
        authors=[
            Author("Brown, Alice", given_name="Alice", family_name="Brown"),
        ],
        year=2022,
        doi="10.1000/example.2022.002",
        journal="Physics Today",
        source="orcid",
    )

    pub4 = Publication(
        title="Deep Learning Methods for Computational Physics",  # more different
        authors=[
            Author("Brown, A.", given_name="A.", family_name="Brown"),
        ],
        year=2021,  # different year
        journal="Computer Physics",  # different journal
        source="zotero",
    )

    pub5 = Publication(
        title="Quantum Computing Fundamentals",
        authors=[
            Author("Wilson, Bob", given_name="Bob", family_name="Wilson"),
        ],
        year=2021,
        doi="10.1000/example.2021.003",
        journal="Quantum Review",
        source="orcid",
    )

    return [pub1, pub2, pub3, pub4, pub5]


@pytest.fixture
def matcher():
    """Create a matcher instance for testing."""
    return PublicationMatcher()


class TestPublicationMatcher:
    """Test cases for PublicationMatcher class."""

    def test_exact_doi_match(self, matcher, sample_publications):
        """Test exact DOI matching between publications."""
        pub1, pub2 = sample_publications[0], sample_publications[1]
        
        # Should match based on identical DOI
        result = matcher.match_publications(pub1, pub2)
        assert result.is_match is True
        assert result.confidence >= 1.0
        assert "doi" in result.match_reasons

    def test_title_normalization_match(self, matcher, sample_publications):
        """Test title-based matching with normalization."""
        pub1, pub2 = sample_publications[0], sample_publications[1]
        
        # Remove DOIs to test title matching
        pub1_no_doi = Publication(
            title=pub1.title,
            authors=pub1.authors,
            year=pub1.year,
            journal=pub1.journal,
            source=pub1.source,
        )
        pub2_no_doi = Publication(
            title=pub2.title,  # lowercase version
            authors=pub2.authors,
            year=pub2.year,
            journal=pub2.journal,
            source=pub2.source,
        )
        
        result = matcher.match_publications(pub1_no_doi, pub2_no_doi)
        assert result.is_match is True
        assert result.confidence > 0.8
        assert "title" in result.match_reasons

    def test_partial_title_match(self, matcher, sample_publications):
        """Test partial title matching."""
        pub3, pub4 = sample_publications[2], sample_publications[3]
        
        result = matcher.match_publications(pub3, pub4)
        # Should be a potential match but not exact
        assert result.is_match is False
        assert 0.2 <= result.confidence < 0.8  # Lower expectation
        assert "authors" in result.match_reasons  # Still matches on authors

    def test_author_name_variations(self, matcher):
        """Test author name variation handling."""
        pub1 = Publication(
            title="Test Publication",
            authors=[Author("Smith, John A.", given_name="John A.", family_name="Smith")],
            year=2023,
            source="orcid",
        )
        
        pub2 = Publication(
            title="Test Publication",
            authors=[Author("Smith, J. A.", given_name="J. A.", family_name="Smith")],
            year=2023,
            source="zotero",
        )
        
        result = matcher.match_publications(pub1, pub2)
        assert result.is_match is True
        assert result.confidence > 0.8
        assert "authors" in result.match_reasons

    def test_year_tolerance(self, matcher):
        """Test year tolerance in matching."""
        pub1 = Publication(
            title="Test Publication",
            authors=[Author("Smith, John", given_name="John", family_name="Smith")],
            year=2022,
            source="orcid",
        )
        
        pub2 = Publication(
            title="Test Publication",
            authors=[Author("Smith, John", given_name="John", family_name="Smith")],
            year=2023,  # +1 year difference
            source="zotero",
        )
        
        result = matcher.match_publications(pub1, pub2)
        assert result.is_match is True  # Should match with year tolerance
        assert result.confidence > 0.7

    def test_different_dois_no_match(self, matcher):
        """Test that different DOIs prevent matching."""
        pub1 = Publication(
            title="Same Title",
            authors=[Author("Smith, John", given_name="John", family_name="Smith")],
            year=2023,
            doi="10.1000/example.001",
            source="orcid",
        )
        
        pub2 = Publication(
            title="Same Title",
            authors=[Author("Smith, John", given_name="John", family_name="Smith")],
            year=2023,
            doi="10.1000/example.002",  # Different DOI
            source="zotero",
        )
        
        result = matcher.match_publications(pub1, pub2)
        assert result.is_match is False
        assert result.confidence == 0.0

    def test_find_missing_publications(self, matcher, sample_publications):
        """Test finding missing publications."""
        source_pubs = [sample_publications[0], sample_publications[2], sample_publications[4]]
        reference_pubs = [sample_publications[1]]  # Only one matching publication
        
        missing = matcher.find_missing(source_pubs, reference_pubs)
        
        # Should find 2 missing publications (indexes 2 and 4)
        assert len(missing) == 2
        assert sample_publications[2] in missing
        assert sample_publications[4] in missing

    def test_find_duplicates(self, matcher, sample_publications):
        """Test finding duplicates within a collection."""
        pubs_with_duplicates = [
            sample_publications[0],  # Original
            sample_publications[1],  # Duplicate of first
            sample_publications[2],  # Unique
        ]
        
        duplicates = matcher.find_duplicates(pubs_with_duplicates)
        
        assert len(duplicates) == 1
        assert len(duplicates[0]) == 2  # Two publications in duplicate group
        assert sample_publications[0] in duplicates[0]
        assert sample_publications[1] in duplicates[0]

    def test_find_potential_matches(self, matcher, sample_publications):
        """Test finding potential matches with confidence scores."""
        # Create a better potential match case
        source_pub = Publication(
            title="Machine Learning for Scientific Computing",  # Similar to pub1
            authors=[Author("Smith, J.", given_name="J.", family_name="Smith")],
            year=2023,
            journal="Journal of Science",
            source="orcid",
        )
        
        reference_pub = Publication(
            title="Machine Learning in Scientific Computing",
            authors=[Author("Smith, John", given_name="John", family_name="Smith")],
            year=2023,
            journal="Science Journal",  # Different journal
            source="zotero",
        )
        
        potential_matches = matcher.find_potential_matches([source_pub], [reference_pub])
        
        assert len(potential_matches) == 1
        match = potential_matches[0]
        assert match.source_publication == source_pub
        assert match.reference_publication == reference_pub
        assert 0.5 <= match.confidence < 0.8

    def test_confidence_scoring(self, matcher):
        """Test confidence scoring algorithm."""
        # Perfect match
        pub1 = Publication(
            title="Exact Title",
            authors=[Author("Smith, John", given_name="John", family_name="Smith")],
            year=2023,
            doi="10.1000/test.001",
            source="orcid",
        )
        
        pub2 = Publication(
            title="Exact Title",
            authors=[Author("Smith, John", given_name="John", family_name="Smith")],
            year=2023,
            doi="10.1000/test.001",
            source="zotero",
        )
        
        result = matcher.match_publications(pub1, pub2)
        assert result.confidence >= 1.0

    def test_empty_publication_lists(self, matcher):
        """Test handling of empty publication lists."""
        empty_list = []
        sample_list = [Publication(
            title="Test",
            authors=[Author("Test", family_name="Test")],
            year=2023,
            source="test",
        )]
        
        # Empty source list
        missing = matcher.find_missing(empty_list, sample_list)
        assert missing == []
        
        # Empty reference list
        missing = matcher.find_missing(sample_list, empty_list)
        assert len(missing) == 1
        
        # Empty duplicate search
        duplicates = matcher.find_duplicates(empty_list)
        assert duplicates == []

    def test_custom_threshold(self):
        """Test custom similarity threshold."""
        strict_matcher = PublicationMatcher(similarity_threshold=0.95)
        
        pub1 = Publication(
            title="Machine Learning Applications",
            authors=[Author("Smith, J.", family_name="Smith")],
            year=2023,
            source="orcid",
        )
        
        pub2 = Publication(
            title="Machine Learning Applications in Science",  # Slightly different
            authors=[Author("Smith, John", family_name="Smith")],
            year=2023,
            source="zotero",
        )
        
        result = strict_matcher.match_publications(pub1, pub2)
        assert result.is_match is False  # Should not match with strict threshold

    def test_journal_matching_bonus(self, matcher):
        """Test that matching journals increase confidence."""
        pub1 = Publication(
            title="Test Title",
            authors=[Author("Smith, J.", family_name="Smith")],
            year=2023,
            journal="Nature",
            source="orcid",
        )
        
        pub2_same_journal = Publication(
            title="Test Title",
            authors=[Author("Smith, J.", family_name="Smith")],
            year=2023,
            journal="Nature",  # Same journal
            source="zotero",
        )
        
        pub2_diff_journal = Publication(
            title="Test Title",
            authors=[Author("Smith, J.", family_name="Smith")],
            year=2023,
            journal="Science",  # Different journal
            source="zotero",
        )
        
        result_same = matcher.match_publications(pub1, pub2_same_journal)
        result_diff = matcher.match_publications(pub1, pub2_diff_journal)
        
        assert result_same.confidence > result_diff.confidence


class TestMatchResult:
    """Test cases for MatchResult class."""

    def test_match_result_creation(self):
        """Test MatchResult creation and properties."""
        pub1 = Publication(title="Test 1", authors=[Author("A")], year=2023, source="test")
        pub2 = Publication(title="Test 2", authors=[Author("B")], year=2023, source="test")
        
        result = MatchResult(
            source_publication=pub1,
            reference_publication=pub2,
            confidence=0.85,
            is_match=True,
            match_reasons=["title", "year"],
        )
        
        assert result.source_publication == pub1
        assert result.reference_publication == pub2
        assert result.confidence == 0.85
        assert result.is_match is True
        assert result.match_reasons == ["title", "year"]

    def test_match_result_string_representation(self):
        """Test MatchResult string representation."""
        pub1 = Publication(title="Test 1", authors=[Author("A")], year=2023, source="test")
        pub2 = Publication(title="Test 2", authors=[Author("B")], year=2023, source="test")
        
        result = MatchResult(
            source_publication=pub1,
            reference_publication=pub2,
            confidence=0.85,
            is_match=True,
            match_reasons=["title"],
        )
        
        str_repr = str(result)
        assert "Match" in str_repr
        assert "85%" in str_repr or "0.85" in str_repr