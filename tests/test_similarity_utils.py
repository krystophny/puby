"""Tests for similarity_utils module."""

import pytest

from puby.similarity_utils import (
    calculate_author_set_similarity,
    calculate_enhanced_title_similarity,
    calculate_jaccard_similarity,
    calculate_simple_similarity,
    calculate_title_similarity_with_length_penalty,
    normalize_text,
)


class TestNormalizeText:
    """Test normalize_text function."""
    
    def test_empty_text(self):
        """Test with empty string."""
        assert normalize_text("") == ""
        
    def test_none_text(self):
        """Test with None."""
        assert normalize_text(None) == ""
        
    def test_basic_normalization(self):
        """Test basic text normalization."""
        result = normalize_text("Hello, World!")
        assert result == "hello world"
        
    def test_punctuation_removal(self):
        """Test punctuation is removed."""
        result = normalize_text("Test: with-various; punctuation!")
        assert result == "test with various punctuation"
        
    def test_extra_spaces_collapsed(self):
        """Test multiple spaces are collapsed."""
        result = normalize_text("multiple    spaces   here")
        assert result == "multiple spaces here"
        
    def test_leading_trailing_spaces(self):
        """Test leading and trailing spaces are removed."""
        result = normalize_text("  padded text  ")
        assert result == "padded text"


class TestCalculateJaccardSimilarity:
    """Test calculate_jaccard_similarity function."""
    
    def test_empty_sets(self):
        """Test with empty sets."""
        assert calculate_jaccard_similarity(set(), set()) == 0.0
        assert calculate_jaccard_similarity({"word"}, set()) == 0.0
        assert calculate_jaccard_similarity(set(), {"word"}) == 0.0
        
    def test_identical_sets(self):
        """Test with identical sets."""
        words = {"hello", "world"}
        assert calculate_jaccard_similarity(words, words) == 1.0
        
    def test_no_overlap(self):
        """Test with no overlapping words."""
        words1 = {"hello", "world"}
        words2 = {"foo", "bar"}
        assert calculate_jaccard_similarity(words1, words2) == 0.0
        
    def test_partial_overlap(self):
        """Test with partial overlap."""
        words1 = {"hello", "world", "test"}
        words2 = {"world", "foo", "bar"}
        # Intersection: 1, Union: 5, Expected: 1/5 = 0.2
        assert calculate_jaccard_similarity(words1, words2) == 0.2
        
    def test_complete_overlap_different_sizes(self):
        """Test when smaller set is completely contained in larger."""
        words1 = {"hello", "world"}
        words2 = {"hello", "world", "extra"}
        # Intersection: 2, Union: 3, Expected: 2/3
        expected = 2.0 / 3.0
        assert abs(calculate_jaccard_similarity(words1, words2) - expected) < 1e-10


class TestCalculateSimpleSimilarity:
    """Test calculate_simple_similarity function."""
    
    def test_empty_strings(self):
        """Test with empty strings."""
        assert calculate_simple_similarity("", "") == 0.0
        assert calculate_simple_similarity("hello", "") == 0.0
        assert calculate_simple_similarity("", "world") == 0.0
        
    def test_identical_strings(self):
        """Test with identical strings."""
        assert calculate_simple_similarity("hello world", "hello world") == 1.0
        
    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert calculate_simple_similarity("Hello World", "hello world") == 1.0
        
    def test_different_strings(self):
        """Test with completely different strings."""
        assert calculate_simple_similarity("hello world", "foo bar") == 0.0
        
    def test_partial_overlap(self):
        """Test with partial word overlap."""
        result = calculate_simple_similarity("hello world test", "world foo bar")
        # Intersection: 1 (world), Union: 5, Expected: 1/5 = 0.2
        assert result == 0.2


class TestCalculateEnhancedTitleSimilarity:
    """Test calculate_enhanced_title_similarity function."""
    
    def test_empty_titles(self):
        """Test with empty titles."""
        assert calculate_enhanced_title_similarity("", "") == 0.0
        assert calculate_enhanced_title_similarity("hello", "") == 0.0
        
    def test_identical_titles(self):
        """Test with identical titles."""
        title = "machine learning algorithms"
        assert calculate_enhanced_title_similarity(title, title) == 1.0
        
    def test_simple_jaccard(self):
        """Test basic Jaccard similarity for short titles."""
        title1 = "hello world"
        title2 = "world foo"
        # Intersection: 1, Union: 3, Expected: 1/3
        result = calculate_enhanced_title_similarity(title1, title2)
        assert abs(result - 1.0/3.0) < 1e-10
        
    def test_substring_containment(self):
        """Test substring containment for longer titles."""
        title1 = "machine learning algorithms"  # 26 chars
        title2 = "deep learning and machine learning algorithms in practice"
        
        # Should get enhanced score due to substring containment
        result = calculate_enhanced_title_similarity(title1, title2)
        basic_jaccard = 3.0 / 7.0  # 3 common words (machine, learning, algorithms) out of 7 total
        
        # Should be higher than basic Jaccard due to enhancement
        assert result > basic_jaccard
        
    def test_word_subset_enhancement(self):
        """Test word subset enhancement for longer titles."""
        title1 = "machine learning"  # 16 chars
        title2 = "advanced machine learning techniques for data science"
        
        # All words from title1 are in title2
        result = calculate_enhanced_title_similarity(title1, title2)
        basic_jaccard = 2.0 / 7.0  # 2 common words out of 7 total
        
        # Should be higher than basic Jaccard due to word subset enhancement
        assert result > basic_jaccard
        
    def test_significant_intersection_boost(self):
        """Test boost for significant word intersection."""
        title1 = "machine learning data science"
        title2 = "data science machine learning"
        
        # 4 common words, intersection/min ratio = 4/4 = 1.0 >= 0.5
        # Should get boost factor
        result = calculate_enhanced_title_similarity(title1, title2)
        assert result == 1.0  # Perfect match after boost


class TestCalculateTitleSimilarityWithLengthPenalty:
    """Test calculate_title_similarity_with_length_penalty function."""
    
    def test_empty_titles(self):
        """Test with empty titles."""
        assert calculate_title_similarity_with_length_penalty("", "") == 0.0
        
    def test_identical_normalized_titles(self):
        """Test with titles that normalize to identical."""
        result = calculate_title_similarity_with_length_penalty(
            "Hello, World!", "hello world"
        )
        assert result == 1.0
        
    def test_length_penalty_applied(self):
        """Test that length penalty is applied."""
        # Same words but different lengths
        title1 = "machine learning"  # 2 words
        title2 = "machine learning algorithms data"  # 4 words
        
        result = calculate_title_similarity_with_length_penalty(title1, title2)
        basic_jaccard = 2.0 / 4.0  # 2 intersection, 4 union = 0.5
        length_penalty = 2.0 / 4.0  # min/max = 0.5
        expected = basic_jaccard * length_penalty  # 0.5 * 0.5 = 0.25
        
        assert abs(result - expected) < 1e-10


class TestCalculateAuthorSetSimilarity:
    """Test calculate_author_set_similarity function."""
    
    def test_empty_sets(self):
        """Test with empty author name sets."""
        assert calculate_author_set_similarity(set(), set()) == 0.0
        assert calculate_author_set_similarity({"Smith, J"}, set()) == 0.0
        
    def test_identical_authors(self):
        """Test with identical author sets."""
        authors = {"Smith, J", "Doe, J"}
        assert calculate_author_set_similarity(authors, authors) == 1.0
        
    def test_no_common_authors(self):
        """Test with no common authors."""
        authors1 = {"Smith, J", "Doe, J"}
        authors2 = {"Brown, A", "Wilson, B"}
        assert calculate_author_set_similarity(authors1, authors2) == 0.0
        
    def test_partial_author_overlap(self):
        """Test with partial author overlap."""
        authors1 = {"Smith, J", "Doe, J", "Brown, A"}
        authors2 = {"Doe, J", "Wilson, B", "Taylor, C"}
        # Intersection: 1, Union: 5, Expected: 1/5 = 0.2
        result = calculate_author_set_similarity(authors1, authors2)
        assert result == 0.2