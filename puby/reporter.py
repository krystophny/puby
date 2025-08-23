"""Reporting utilities for publication analysis results."""

from typing import List, Tuple
import json
import csv
from io import StringIO

import click
from tabulate import tabulate

from .models import Publication


class ConsoleReporter:
    """Report analysis results to console."""
    
    def __init__(self, format: str = "table"):
        """Initialize reporter with output format."""
        self.format = format
    
    def report_missing(self, publications: List[Publication]):
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
    
    def report_duplicates(self, duplicate_groups: List[List[Publication]]):
        """Report duplicate publications."""
        if not duplicate_groups:
            click.echo("\n✓ No duplicates found in Zotero.")
            return
        
        total_dups = sum(len(group) for group in duplicate_groups)
        click.echo(f"\n⚠ Found {len(duplicate_groups)} group(s) of duplicates ({total_dups} total):")
        click.echo("-" * 60)
        
        for i, group in enumerate(duplicate_groups, 1):
            click.echo(f"\nDuplicate Group {i}:")
            if self.format == "table":
                self._print_table(group)
            else:
                for pub in group:
                    click.echo(f"  - {pub}")
    
    def report_potential_matches(
        self, 
        matches: List[Tuple[Publication, Publication, float]]
    ):
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
    
    def _print_table(self, publications: List[Publication]):
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
            doi = pub.doi[:20] + "..." if pub.doi and len(pub.doi) > 20 else (pub.doi or "-")
            
            rows.append([
                pub.year or "-",
                authors,
                title,
                journal,
                doi
            ])
        
        click.echo(tabulate(rows, headers=headers, tablefmt="grid"))
    
    def _print_json(self, publications: List[Publication]):
        """Print publications as JSON."""
        data = []
        for pub in publications:
            data.append({
                "title": pub.title,
                "authors": [str(a) for a in pub.authors],
                "year": pub.year,
                "journal": pub.journal,
                "doi": pub.doi,
                "url": pub.url,
                "source": pub.source
            })
        
        click.echo(json.dumps(data, indent=2))
    
    def _print_csv(self, publications: List[Publication]):
        """Print publications as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Title", "Authors", "Year", "Journal", "DOI", "URL", "Source"])
        
        # Write data
        for pub in publications:
            authors = "; ".join(str(a) for a in pub.authors)
            writer.writerow([
                pub.title,
                authors,
                pub.year or "",
                pub.journal or "",
                pub.doi or "",
                pub.url or "",
                pub.source or ""
            ])
        
        click.echo(output.getvalue())
    
    def _print_bibtex(self, publications: List[Publication]):
        """Print publications as BibTeX."""
        for pub in publications:
            click.echo(pub.to_bibtex())
            click.echo()  # Empty line between entries