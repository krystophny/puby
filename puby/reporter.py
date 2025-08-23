"""Reporting utilities for publication analysis results."""

import csv
import json
from dataclasses import dataclass
from io import StringIO
from typing import Dict, List, Tuple

import click
from tabulate import tabulate

from .matcher import PotentialMatch
from .models import Publication


class ConsoleReporter:
    """Report analysis results to console."""

    def __init__(self, format: str = "table") -> None:
        """Initialize reporter with output format."""
        self.format = format

    def report_missing(self, publications: List[Publication]) -> None:
        """Report missing publications."""
        if not publications:
            click.echo("\n✓ No missing publications found.")
            return

        click.echo(f"\n⚠ Found {len(publications)} missing publication(s) in Zotero:")
        click.echo("-" * 60)

        if self.format == "table":
            self._print_table(publications)
        elif self.format == "json":
            self._print_json(publications)
        elif self.format == "csv":
            self._print_csv(publications)
        elif self.format == "bibtex":
            self._print_bibtex(publications)

    def report_duplicates(self, duplicate_groups: List[List[Publication]]) -> None:
        """Report duplicate publications."""
        if not duplicate_groups:
            click.echo("\n✓ No duplicates found in Zotero.")
            return

        total_dups = sum(len(group) for group in duplicate_groups)
        click.echo(
            f"\n⚠ Found {len(duplicate_groups)} group(s) of duplicates ({total_dups} total):"
        )
        click.echo("-" * 60)

        for i, group in enumerate(duplicate_groups, 1):
            click.echo(f"\nDuplicate Group {i}:")
            if self.format == "table":
                self._print_table(group)
            else:
                for pub in group:
                    click.echo(f"  - {pub}")

    def report_potential_matches(
        self, matches: List[Tuple[Publication, Publication, float]]
    ) -> None:
        """Report potential matches that need review."""
        if not matches:
            click.echo("\n✓ No ambiguous matches found.")
            return

        click.echo(f"\n⚠ Found {len(matches)} potential match(es) to review:")
        click.echo("-" * 60)

        for source_pub, ref_pub, similarity in matches[:10]:  # Limit to top 10
            click.echo(f"\nSimilarity: {similarity:.2%}")
            click.echo(f"Source: {source_pub}")
            click.echo(f"Zotero: {ref_pub}")

    def _print_table(self, publications: List[Publication]) -> None:
        """Print publications as a formatted table."""
        if not publications:
            return

        headers = ["Year", "Authors", "Title", "Journal", "DOI"]
        rows = []

        for pub in publications:
            # Format authors
            if pub.authors:
                if len(pub.authors) <= 2:
                    authors = ", ".join(str(a) for a in pub.authors)
                else:
                    authors = f"{pub.authors[0]} et al."
            else:
                authors = "[No authors]"

            # Truncate title if too long
            title = pub.title[:50] + "..." if len(pub.title) > 50 else pub.title

            # Format journal
            journal = pub.journal[:30] if pub.journal else "-"

            # Format DOI
            doi = (
                pub.doi[:20] + "..."
                if pub.doi and len(pub.doi) > 20
                else (pub.doi or "-")
            )

            rows.append([pub.year or "-", authors, title, journal, doi])

        click.echo(tabulate(rows, headers=headers, tablefmt="grid"))

    def _print_json(self, publications: List[Publication]) -> None:
        """Print publications as JSON."""
        data = []
        for pub in publications:
            data.append(
                {
                    "title": pub.title,
                    "authors": [str(a) for a in pub.authors],
                    "year": pub.year,
                    "journal": pub.journal,
                    "doi": pub.doi,
                    "url": pub.url,
                    "source": pub.source,
                }
            )

        click.echo(json.dumps(data, indent=2))

    def _print_csv(self, publications: List[Publication]) -> None:
        """Print publications as CSV."""
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Title", "Authors", "Year", "Journal", "DOI", "URL", "Source"])

        # Write data
        for pub in publications:
            authors = "; ".join(str(a) for a in pub.authors)
            writer.writerow(
                [
                    pub.title,
                    authors,
                    pub.year or "",
                    pub.journal or "",
                    pub.doi or "",
                    pub.url or "",
                    pub.source or "",
                ]
            )

        click.echo(output.getvalue())

    def _print_bibtex(self, publications: List[Publication]) -> None:
        """Print publications as BibTeX."""
        for pub in publications:
            click.echo(pub.to_bibtex())
            click.echo()  # Empty line between entries


@dataclass
class AnalysisResult:
    """Complete analysis result with all findings."""

    missing_publications: List[Publication]
    duplicate_groups: List[List[Publication]]
    potential_matches: List[PotentialMatch]
    total_source_publications: int
    total_reference_publications: int


@dataclass
class SyncRecommendation:
    """Recommendation for synchronizing publication libraries."""

    action_type: str  # "add", "remove", "merge", "review"
    publication: Publication
    reason: str
    confidence: float


class AnalysisReporter:
    """Generate comprehensive analysis reports with recommendations."""

    def __init__(self, format: str = "table", verbose: bool = False) -> None:
        """Initialize analysis reporter.

        Args:
            format: Output format (table, json, csv, bibtex)
            verbose: Include detailed information in output
        """
        self.format = format
        self.verbose = verbose
        self.console_reporter = ConsoleReporter(format)

    def generate_full_report(self, result: AnalysisResult) -> None:
        """Generate complete analysis report with all sections.

        Args:
            result: Analysis result containing all findings
        """
        self._print_header()
        self._print_missing_section(result.missing_publications)
        self._print_duplicates_section(result.duplicate_groups)
        self._print_potential_matches_section(result.potential_matches)
        self._print_summary_statistics(result)

        # Generate and display sync recommendations
        recommendations = self.generate_sync_recommendations(result)
        self.print_sync_recommendations(recommendations)

    def generate_sync_recommendations(
        self, result: AnalysisResult
    ) -> List[SyncRecommendation]:
        """Generate actionable sync recommendations.

        Args:
            result: Analysis result to base recommendations on

        Returns:
            List of sync recommendations
        """
        recommendations = []

        # Recommend adding missing publications
        for pub in result.missing_publications:
            recommendations.append(
                SyncRecommendation(
                    action_type="add",
                    publication=pub,
                    reason="Missing in reference library",
                    confidence=0.95,
                )
            )

        # Recommend merging or removing duplicates
        for group in result.duplicate_groups:
            if len(group) > 1:
                # Keep the most complete publication, remove others
                primary = self._select_primary_publication(group)
                for pub in group:
                    if pub != primary:
                        recommendations.append(
                            SyncRecommendation(
                                action_type="remove",
                                publication=pub,
                                reason="Duplicate of better entry",
                                confidence=0.85,
                            )
                        )

        # Recommend reviewing potential matches
        for match in result.potential_matches[:5]:  # Limit to top 5
            recommendations.append(
                SyncRecommendation(
                    action_type="review",
                    publication=match.source_publication,
                    reason=f"Potential match with {match.confidence:.0%} confidence",
                    confidence=match.confidence,
                )
            )

        return recommendations

    def print_sync_recommendations(self, recommendations: List[SyncRecommendation]) -> None:
        """Print formatted sync recommendations.

        Args:
            recommendations: List of recommendations to display
        """
        if not recommendations:
            click.echo("\n✓ No sync recommendations needed.")
            return

        click.echo("\n" + "=" * 60)
        click.echo("SYNC RECOMMENDATIONS")
        click.echo("=" * 60)

        # Group by action type
        by_action: Dict[str, List[SyncRecommendation]] = {}
        for rec in recommendations:
            if rec.action_type not in by_action:
                by_action[rec.action_type] = []
            by_action[rec.action_type].append(rec)

        for action_type, recs in by_action.items():
            action_name = action_type.upper()
            click.echo(f"\n{action_name} ({len(recs)} items):")
            click.echo("-" * 40)

            for rec in recs:
                confidence_pct = int(rec.confidence * 100)
                click.echo(f"• {rec.reason} ({confidence_pct}% confidence)")
                if self.verbose:
                    click.echo(f"  Publication: {rec.publication.title[:60]}...")
                    if rec.publication.authors:
                        author_str = ", ".join(
                            str(a) for a in rec.publication.authors[:2]
                        )
                        click.echo(f"  Authors: {author_str}")
                    click.echo(f"  Year: {rec.publication.year or 'Unknown'}")
                    click.echo()

    def _print_header(self) -> None:
        """Print report header."""
        click.echo("\n" + "=" * 60)
        click.echo("PUBLICATION ANALYSIS REPORT")
        click.echo("=" * 60)

    def _print_missing_section(self, missing_publications: List[Publication]) -> None:
        """Print missing publications section.

        Args:
            missing_publications: List of missing publications
        """
        click.echo("\nMissing Publications:")
        self.console_reporter.report_missing(missing_publications)

    def _print_duplicates_section(self, duplicate_groups: List[List[Publication]]) -> None:
        """Print duplicates section.

        Args:
            duplicate_groups: List of duplicate groups
        """
        click.echo("\nDuplicate Publications:")
        self.console_reporter.report_duplicates(duplicate_groups)

    def _print_potential_matches_section(self, potential_matches: List[PotentialMatch]) -> None:
        """Print potential matches section.

        Args:
            potential_matches: List of potential matches
        """
        click.echo("\nPotential Matches for Review:")
        # Convert to the format expected by console reporter
        tuples = [
            (m.source_publication, m.reference_publication, m.confidence)
            for m in potential_matches
        ]
        self.console_reporter.report_potential_matches(tuples)

    def _print_summary_statistics(self, result: AnalysisResult) -> None:
        """Print summary statistics.

        Args:
            result: Analysis result with statistics
        """
        click.echo("\n" + "=" * 60)
        click.echo("SUMMARY STATISTICS")
        click.echo("=" * 60)

        total_missing = len(result.missing_publications)
        total_duplicates = sum(len(group) for group in result.duplicate_groups)
        total_potential = len(result.potential_matches)

        click.echo(f"Source Publications: {result.total_source_publications}")
        click.echo(f"Reference Publications: {result.total_reference_publications}")
        click.echo(f"Missing Publications: {total_missing}")
        click.echo(f"Duplicate Publications: {total_duplicates}")
        click.echo(f"Potential Matches: {total_potential}")

        if result.total_source_publications > 0:
            missing_pct = (total_missing / result.total_source_publications) * 100
            click.echo(f"Missing Percentage: {missing_pct:.1f}%")

        if result.total_reference_publications > 0:
            dup_pct = (total_duplicates / result.total_reference_publications) * 100
            click.echo(f"Duplicate Percentage: {dup_pct:.1f}%")

        click.echo("\n" + "=" * 60)

        # Print actionable summary
        if total_missing > 0 or total_duplicates > 0 or total_potential > 0:
            click.echo("\n📋 Action Items:")
            if total_missing > 0:
                click.echo(f"  • Add {total_missing} missing publication(s) to library")
            if total_duplicates > 0:
                click.echo(f"  • Review and merge {total_duplicates} duplicate(s)")
            if total_potential > 0:
                click.echo(f"  • Review {total_potential} potential match(es)")
        else:
            click.echo("\n✓ Your publication libraries are in sync!")

    def _select_primary_publication(
        self, publications: List[Publication]
    ) -> Publication:
        """Select the most complete publication from a group.

        Args:
            publications: List of duplicate publications

        Returns:
            The publication with the most complete information
        """
        if not publications:
            raise ValueError("Cannot select from empty list")

        def completeness_score(pub: Publication) -> int:
            """Calculate completeness score for a publication."""
            score = 0
            if pub.title:
                score += 1
            if pub.authors:
                score += len(pub.authors)
            if pub.year:
                score += 1
            if pub.doi:
                score += 2  # DOI is more valuable
            if pub.journal:
                score += 1
            if pub.abstract:
                score += 1
            if pub.url:
                score += 1
            return score

        return max(publications, key=completeness_score)
