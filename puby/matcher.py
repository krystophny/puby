"""Publication matching and comparison utilities."""

import re
from dataclasses import dataclass
from typing import List, Optional

from .models import Author, Publication


@dataclass
class MatchResult:
    """Result of matching two publications."""

    source_publication: Publication
    reference_publication: Publication
    confidence: float
    is_match: bool
    match_reasons: List[str]

    def __str__(self) -> str:
        """Return string representation of match result."""
        match_status = "Match" if self.is_match else "No Match"
        confidence_pct = int(self.confidence * 100)
        reasons = ", ".join(self.match_reasons) if self.match_reasons else "none"
        return f"{match_status} ({confidence_pct}% confidence) - " f"Reasons: {reasons}"


@dataclass
class PotentialMatch:
    """A potential match between publications with confidence score."""

    source_publication: Publication
    reference_publication: Publication
    confidence: float


class PublicationMatcher:
    """Match and compare publications across different sources."""

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        year_tolerance: int = 1,
        potential_threshold: float = 0.5,
    ):
        """Initialize the matcher with configuration.

        Args:
            similarity_threshold: Minimum confidence for exact matches
            year_tolerance: Maximum year difference for matches
            potential_threshold: Minimum confidence for potential matches
        """
        self.similarity_threshold = similarity_threshold
        self.year_tolerance = year_tolerance
        self.potential_threshold = potential_threshold

    def match_publications(self, pub1: Publication, pub2: Publication) -> MatchResult:
        """Match two publications and return detailed result."""
        # Check for definitive DOI match first
        doi_result = self._check_doi_match(pub1, pub2)
        if doi_result:
            return doi_result

        # Calculate similarity based on multiple factors
        confidence, reasons = self._calculate_similarity(pub1, pub2)
        is_match = confidence >= self.similarity_threshold

        return MatchResult(
            source_publication=pub1,
            reference_publication=pub2,
            confidence=min(confidence, 1.0),
            is_match=is_match,
            match_reasons=reasons,
        )

    def _check_doi_match(
        self, pub1: Publication, pub2: Publication
    ) -> Optional[MatchResult]:
        """Check for definitive DOI match between publications."""
        if pub1.doi and pub2.doi:
            if self._normalize_doi(pub1.doi) == self._normalize_doi(pub2.doi):
                return MatchResult(
                    source_publication=pub1,
                    reference_publication=pub2,
                    confidence=1.0,
                    is_match=True,
                    match_reasons=["doi"],
                )
            else:
                # Different DOIs mean different publications
                return MatchResult(
                    source_publication=pub1,
                    reference_publication=pub2,
                    confidence=0.0,
                    is_match=False,
                    match_reasons=[],
                )
        return None

    def _calculate_similarity(
        self, pub1: Publication, pub2: Publication
    ) -> tuple[float, List[str]]:
        """Calculate similarity score and reasons between two publications."""
        confidence = 0.0
        reasons = []

        # Title similarity (weighted heavily)
        if pub1.title and pub2.title:
            title_sim = self._calculate_title_similarity(pub1.title, pub2.title)
            if title_sim > 0.6:
                confidence += title_sim * 0.5
                reasons.append("title")

        # Year matching with tolerance
        if pub1.year and pub2.year:
            year_diff = abs(pub1.year - pub2.year)
            if year_diff <= self.year_tolerance:
                year_score = max(0, 1.0 - (year_diff / (self.year_tolerance + 1)))
                confidence += year_score * 0.2
                reasons.append("year")

        # Author similarity
        if pub1.authors and pub2.authors:
            author_sim = self._calculate_author_similarity(pub1.authors, pub2.authors)
            if author_sim > 0.3:
                confidence += author_sim * 0.2
                reasons.append("authors")

        # Journal bonus
        if (
            pub1.journal
            and pub2.journal
            and self._normalize_text(pub1.journal) == self._normalize_text(pub2.journal)
        ):
            confidence += 0.1
            reasons.append("journal")

        return confidence, reasons

    def find_missing(
        self, source_pubs: List[Publication], reference_pubs: List[Publication]
    ) -> List[Publication]:
        """Find publications in source that are missing from reference."""
        if not source_pubs:
            return []
        if not reference_pubs:
            return list(source_pubs)

        missing = []
        for source_pub in source_pubs:
            found = False
            for ref_pub in reference_pubs:
                result = self.match_publications(source_pub, ref_pub)
                if result.is_match:
                    found = True
                    break
            if not found:
                missing.append(source_pub)

        return missing

    def find_duplicates(
        self, publications: List[Publication]
    ) -> List[List[Publication]]:
        """Find duplicate publications within a list."""
        if not publications:
            return []

        duplicates = []
        seen = set()

        for i, pub1 in enumerate(publications):
            if i in seen:
                continue

            group = [pub1]
            for j, pub2 in enumerate(publications[i + 1 :], start=i + 1):
                if j not in seen:
                    result = self.match_publications(pub1, pub2)
                    if result.is_match:
                        group.append(pub2)
                        seen.add(j)

            if len(group) > 1:
                duplicates.append(group)
                seen.add(i)

        return duplicates

    def find_potential_matches(
        self, source_pubs: List[Publication], reference_pubs: List[Publication]
    ) -> List[PotentialMatch]:
        """Find potential matches between source and reference with scores."""
        potential_matches = []

        for source_pub in source_pubs:
            for ref_pub in reference_pubs:
                result = self.match_publications(source_pub, ref_pub)

                # If it's a potential match but not exact
                if (
                    self.potential_threshold
                    <= result.confidence
                    < self.similarity_threshold
                ):
                    potential_matches.append(
                        PotentialMatch(
                            source_publication=source_pub,
                            reference_publication=ref_pub,
                            confidence=result.confidence,
                        )
                    )

        # Sort by confidence score (highest first)
        potential_matches.sort(key=lambda x: x.confidence, reverse=True)

        return potential_matches

    def _normalize_doi(self, doi: str) -> str:
        """Normalize DOI for comparison."""
        return doi.lower().strip()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove punctuation, extra spaces, convert to lowercase
        normalized = re.sub(r"[^\w\s]", " ", text.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """Calculate title similarity with advanced normalization."""
        if not title1 or not title2:
            return 0.0

        # Normalize titles
        norm1 = self._normalize_text(title1)
        norm2 = self._normalize_text(title2)

        if norm1 == norm2:
            return 1.0

        # Word-based Jaccard similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        jaccard = intersection / union if union > 0 else 0.0

        # Penalty for different lengths (more strict)
        len_ratio = min(len(words1), len(words2)) / max(len(words1), len(words2))

        return jaccard * len_ratio

    def _calculate_author_similarity(
        self, authors1: List[Author], authors2: List[Author]
    ) -> float:
        """Calculate author similarity with name variation handling."""
        if not authors1 or not authors2:
            return 0.0

        # Get normalized author names
        names1 = {self._normalize_author_name(author) for author in authors1}
        names2 = {self._normalize_author_name(author) for author in authors2}

        # Calculate Jaccard similarity
        intersection = len(names1 & names2)
        union = len(names1 | names2)

        return intersection / union if union > 0 else 0.0

    def _normalize_author_name(self, author: Author) -> str:
        """Normalize author name for comparison."""
        if author.family_name and author.given_name:
            # Use first initial of given name
            given_initial = author.given_name[0].upper() if author.given_name else ""
            return f"{author.family_name.upper()}, {given_initial}"
        else:
            # Fallback to full name, extract family name and initial
            name_parts = author.name.split()
            if len(name_parts) >= 2:
                # Assume last part is family name
                family = name_parts[-1].upper()
                given_initial = name_parts[0][0].upper() if name_parts[0] else ""
                return f"{family}, {given_initial}"
            else:
                return author.name.upper()
