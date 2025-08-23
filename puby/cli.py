"""Command-line interface for puby."""

import sys
from typing import Optional

import click
from colorama import init as colorama_init

from .client import PublicationClient
from .sources import ORCIDSource, ScholarSource, PureSource, ZoteroLibrary
from .matcher import PublicationMatcher
from .reporter import ConsoleReporter

# Initialize colorama for cross-platform colored output
colorama_init()


@click.group()
@click.version_option(version="0.1.0", prog_name="puby")
def cli():
    """Puby - Publication list management tool for researchers."""
    pass


@cli.command()
@click.option(
    "--scholar",
    help="Google Scholar profile URL",
    type=str,
)
@click.option(
    "--orcid", 
    help="ORCID profile URL (e.g., https://orcid.org/0000-0000-0000-0000)",
    type=str,
)
@click.option(
    "--pure",
    help="Pure research portal URL",
    type=str,
)
@click.option(
    "--zotero",
    required=True,
    help="Zotero group ID or user library ID",
    type=str,
)
@click.option(
    "--api-key",
    help="Zotero API key (required for private libraries)",
    type=str,
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "csv", "bibtex"]),
    default="table",
    help="Output format for results",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def check(
    scholar: Optional[str],
    orcid: Optional[str],
    pure: Optional[str],
    zotero: str,
    api_key: Optional[str],
    format: str,
    verbose: bool,
):
    """Compare publications across sources and identify missing or duplicate entries."""
    
    # Validate that at least one source is provided
    if not any([scholar, orcid, pure]):
        click.echo(
            "Error: At least one source URL (--scholar, --orcid, or --pure) is required.",
            err=True,
        )
        sys.exit(1)
    
    # Initialize the client
    client = PublicationClient(verbose=verbose)
    
    # Initialize sources
    sources = []
    
    if scholar:
        if "scholar.google.com" not in scholar:
            click.echo(f"Error: Invalid Scholar URL: {scholar}", err=True)
            sys.exit(1)
        sources.append(ScholarSource(scholar))
    
    if orcid:
        if "orcid.org" not in orcid:
            click.echo(f"Error: Invalid ORCID URL: {orcid}", err=True)
            sys.exit(1)
        sources.append(ORCIDSource(orcid))
    
    if pure:
        if not pure.startswith("https://"):
            click.echo(f"Error: Pure URL must use HTTPS: {pure}", err=True)
            sys.exit(1)
        sources.append(PureSource(pure))
    
    # Initialize Zotero library
    try:
        zotero_lib = ZoteroLibrary(zotero, api_key=api_key)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    
    # Fetch publications from all sources
    click.echo("Fetching publications from sources...")
    
    all_publications = []
    for source in sources:
        if verbose:
            click.echo(f"  Fetching from {source.__class__.__name__}...")
        pubs = client.fetch_publications(source)
        all_publications.extend(pubs)
        if verbose:
            click.echo(f"    Found {len(pubs)} publications")
    
    # Fetch Zotero publications
    if verbose:
        click.echo(f"  Fetching from Zotero library...")
    zotero_pubs = client.fetch_publications(zotero_lib)
    if verbose:
        click.echo(f"    Found {len(zotero_pubs)} publications")
    
    # Match publications
    click.echo("\nAnalyzing publications...")
    matcher = PublicationMatcher()
    
    # Find missing publications (in sources but not in Zotero)
    missing = matcher.find_missing(all_publications, zotero_pubs)
    
    # Find duplicates within Zotero
    duplicates = matcher.find_duplicates(zotero_pubs)
    
    # Find potential matches (fuzzy matching)
    potential_matches = matcher.find_potential_matches(all_publications, zotero_pubs)
    
    # Report results
    reporter = ConsoleReporter(format=format)
    reporter.report_missing(missing)
    reporter.report_duplicates(duplicates)
    reporter.report_potential_matches(potential_matches)
    
    # Summary
    click.echo("\n" + "=" * 60)
    click.echo(f"Summary:")
    click.echo(f"  Total publications in sources: {len(all_publications)}")
    click.echo(f"  Total publications in Zotero: {len(zotero_pubs)}")
    click.echo(f"  Missing from Zotero: {len(missing)}")
    click.echo(f"  Duplicates in Zotero: {len(duplicates)}")
    click.echo(f"  Potential matches to review: {len(potential_matches)}")


@cli.command()
@click.option(
    "--orcid",
    help="ORCID ID to fetch publications from",
    type=str,
)
@click.option(
    "--output",
    help="Output file path",
    type=str,
    default="publications.bib",
)
def fetch(orcid: Optional[str], output: str):
    """Fetch publications from a source and save to file."""
    
    if not orcid:
        click.echo("Error: --orcid is required for fetch command", err=True)
        sys.exit(1)
    
    client = PublicationClient()
    source = ORCIDSource(orcid)
    
    click.echo(f"Fetching publications from ORCID: {orcid}")
    publications = client.fetch_publications(source)
    
    click.echo(f"Found {len(publications)} publications")
    
    # Save to file (implement based on format)
    click.echo(f"Saving to {output}")
    # TODO: Implement save functionality
    

def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()