"""Shared similarity calculation utilities.

This module provides common similarity calculation functions used across
the codebase to eliminate duplication and ensure consistency.
"""

import re
from typing import List, Set


def normalize_text(text: str) -> str:
    """Normalize text for similarity comparison.
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text with punctuation removed, lowercase, extra spaces collapsed
    """
    if not text:
        return ""
    
    # Remove punctuation, extra spaces, convert to lowercase
    normalized = re.sub(r"[^\w\s]", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def calculate_jaccard_similarity(words1: Set[str], words2: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets of words.
    
    Args:
        words1: First set of words
        words2: Second set of words
        
    Returns:
        Jaccard similarity score (0.0-1.0)
    """
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def calculate_simple_similarity(s1: str, s2: str) -> float:
    """Calculate simple word-based similarity between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity score (0.0-1.0)
    """
    if not s1 or not s2:
        return 0.0
    
    # Normalize and split into words
    words1 = set(s1.lower().split())
    words2 = set(s2.lower().split())
    
    return calculate_jaccard_similarity(words1, words2)


def calculate_enhanced_title_similarity(title1: str, title2: str) -> float:
    """Calculate enhanced fuzzy similarity between two normalized titles.

    Uses word overlap with substring matching for longer titles.

    Args:
        title1: First normalized title
        title2: Second normalized title

    Returns:
        Similarity score (0.0-1.0)
    """
    if not title1 or not title2:
        return 0.0

    # Split into words
    words1 = set(title1.split())
    words2 = set(title2.split())

    if not words1 or not words2:
        return 0.0

    # Calculate basic Jaccard similarity (word overlap)
    jaccard_score = calculate_jaccard_similarity(words1, words2)

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
    intersection = len(words1 & words2)
    if intersection >= 2 and intersection / min(len(words1), len(words2)) >= 0.5:
        # Boost score when at least 2 words match and 50%+ of smaller set matches
        boost_factor = 1.2 if intersection >= 3 else 1.1
        return min(1.0, jaccard_score * boost_factor)

    return jaccard_score


def calculate_title_similarity_with_length_penalty(title1: str, title2: str) -> float:
    """Calculate title similarity with length ratio penalty.
    
    Args:
        title1: First title
        title2: Second title
        
    Returns:
        Similarity score (0.0-1.0) with length penalty applied
    """
    if not title1 or not title2:
        return 0.0

    # Normalize titles
    norm1 = normalize_text(title1)
    norm2 = normalize_text(title2)

    if norm1 == norm2:
        return 1.0

    # Word-based Jaccard similarity
    words1 = set(norm1.split())
    words2 = set(norm2.split())

    if not words1 or not words2:
        return 0.0

    jaccard = calculate_jaccard_similarity(words1, words2)

    # Penalty for different lengths (more strict)
    len_ratio = min(len(words1), len(words2)) / max(len(words1), len(words2))

    return jaccard * len_ratio


def calculate_author_set_similarity(names1: Set[str], names2: Set[str]) -> float:
    """Calculate similarity between two sets of normalized author names.
    
    Args:
        names1: First set of normalized author names
        names2: Second set of normalized author names
        
    Returns:
        Jaccard similarity score (0.0-1.0)
    """
    return calculate_jaccard_similarity(names1, names2)