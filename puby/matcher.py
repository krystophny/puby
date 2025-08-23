"""Publication matching and comparison utilities."""

from typing import List, Tuple, Dict
from collections import defaultdict

from .models import Publication


class PublicationMatcher:
    """Match and compare publications across different sources."""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """Initialize the matcher with similarity threshold."""
        self.similarity_threshold = similarity_threshold
    
    def find_missing(
        self, 
        source_pubs: List[Publication], 
        reference_pubs: List[Publication]
    ) -> List[Publication]:
        """Find publications in source that are missing from reference."""
        missing = []
        
        for source_pub in source_pubs:
            found = False
            for ref_pub in reference_pubs:
                if source_pub.matches(ref_pub, self.similarity_threshold):
                    found = True
                    break
            
            if not found:
                missing.append(source_pub)
        
        return missing
    
    def find_duplicates(self, publications: List[Publication]) -> List[List[Publication]]:
        """Find duplicate publications within a list."""
        duplicates = []
        seen = set()
        
        for i, pub1 in enumerate(publications):
            if i in seen:
                continue
            
            group = [pub1]
            for j, pub2 in enumerate(publications[i+1:], start=i+1):
                if j not in seen and pub1.matches(pub2, self.similarity_threshold):
                    group.append(pub2)
                    seen.add(j)
            
            if len(group) > 1:
                duplicates.append(group)
                seen.add(i)
        
        return duplicates
    
    def find_potential_matches(
        self,
        source_pubs: List[Publication],
        reference_pubs: List[Publication]
    ) -> List[Tuple[Publication, Publication, float]]:
        """Find potential matches between source and reference with similarity scores."""
        potential_matches = []
        
        # Lower threshold for potential matches
        potential_threshold = 0.5
        
        for source_pub in source_pubs:
            for ref_pub in reference_pubs:
                # Calculate similarity
                similarity = self._calculate_similarity(source_pub, ref_pub)
                
                # If it's a potential match but not exact
                if potential_threshold <= similarity < self.similarity_threshold:
                    potential_matches.append((source_pub, ref_pub, similarity))
        
        # Sort by similarity score (highest first)
        potential_matches.sort(key=lambda x: x[2], reverse=True)
        
        return potential_matches
    
    def _calculate_similarity(self, pub1: Publication, pub2: Publication) -> float:
        """Calculate similarity score between two publications."""
        score = 0.0
        weights = {
            "doi": 1.0,
            "title": 0.7,
            "year": 0.2,
            "authors": 0.1
        }
        
        # DOI match is definitive
        if pub1.doi and pub2.doi:
            if pub1.doi.lower() == pub2.doi.lower():
                return 1.0
            else:
                # Different DOIs mean different publications
                return 0.0
        
        # Title similarity
        if pub1.title and pub2.title:
            title_sim = pub1._calculate_similarity(pub1.title, pub2.title)
            score += title_sim * weights["title"]
        
        # Year match
        if pub1.year and pub2.year:
            if pub1.year == pub2.year:
                score += weights["year"]
        
        # Author overlap (simplified)
        if pub1.authors and pub2.authors:
            # Check first author match
            if len(pub1.authors) > 0 and len(pub2.authors) > 0:
                first1 = str(pub1.authors[0]).lower()
                first2 = str(pub2.authors[0]).lower()
                if first1 == first2:
                    score += weights["authors"]
        
        return min(score, 1.0)  # Cap at 1.0