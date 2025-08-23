"""Command-line interface for puby."""

import sys
from typing import List, Optional

import click
from colorama import init as colorama_init

from .client import PublicationClient
from .matcher import PublicationMatcher
from .models import Publication
from .reporter import ConsoleReporter
from .sources import (
    ORCIDSource,
    PublicationSource,
    PureSource,
    ScholarSource,
    ZoteroLibrary,
)

# Initialize colorama for cross-platform colored output
colorama_init()


def _validate_sources(
    scholar: Optional[str], orcid: Optional[str], pure: Optional[str]
) -> None:
    """Validate that at least one source is provided."""
    if not any([scholar, orcid, pure]):
        click.echo(
            "Error: At least one source URL (--scholar, --orcid, or --pure) is required.",
            err=True,
        )
        sys.exit(1)


def _initialize_sources(
    scholar: Optional[str], orcid: Optional[str], pure: Optional[str]
) -> List[PublicationSource]:
    """Initialize and validate publication sources."""
    sources: List[PublicationSource] = []

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

    return sources


def _initialize_zotero(zotero: str, api_key: Optional[str]) -> ZoteroLibrary:
    """Initialize Zotero library with error handling."""
    try:
        return ZoteroLibrary(zotero, api_key=api_key)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _fetch_source_publications(
    client: PublicationClient, sources: List[PublicationSource], verbose: bool
) -> List[Publication]:
    """Fetch publications from all configured sources."""
    click.echo("Fetching publications from sources...")

    all_publications = []
    for source in sources:
        if verbose:
            click.echo(f"  Fetching from {source.__class__.__name__}...")
        pubs = client.fetch_publications(source)
        all_publications.extend(pubs)
        if verbose:
            click.echo(f"    Found {len(pubs)} publications")

    return all_publications


def _fetch_zotero_publications(
    client: PublicationClient, zotero_lib: ZoteroLibrary, verbose: bool
) -> List[Publication]:
    """Fetch publications from Zotero library."""
    if verbose:
        click.echo("  Fetching from Zotero library...")
    zotero_pubs = client.fetch_publications(zotero_lib)
    if verbose:
        click.echo(f"    Found {len(zotero_pubs)} publications")
    return zotero_pubs


def _analyze_publications(
    all_publications: List[Publication], zotero_pubs: List[Publication]
) -> dict:
    """Analyze publications for missing, duplicates and potential matches."""
    click.echo("\nAnalyzing publications...")
    matcher = PublicationMatcher()

    missing = matcher.find_missing(all_publications, zotero_pubs)
    duplicates = matcher.find_duplicates(zotero_pubs)
    potential_matches = matcher.find_potential_matches(all_publications, zotero_pubs)

    return {
        "missing": missing,
        "duplicates": duplicates,
        "potential_matches": potential_matches,
        "all_publications": all_publications,
        "zotero_pubs": zotero_pubs,
    }


def _report_results(analysis_results: dict, format: str) -> None:
    """Report analysis results and summary statistics."""
    reporter = ConsoleReporter(format=format)

    # Report findings
    reporter.report_missing(analysis_results["missing"])
    reporter.report_duplicates(analysis_results["duplicates"])

    # Convert PotentialMatch objects to tuples for reporter
    potential_tuples = [
        (match.source_publication, match.reference_publication, match.confidence)
        for match in analysis_results["potential_matches"]
    ]
    reporter.report_potential_matches(potential_tuples)

    # Print summary
    _print_summary(analysis_results)


def _print_summary(analysis_results: dict) -> None:
    """Print summary statistics."""
    click.echo("\n" + "=" * 60)
    click.echo("Summary:")
    click.echo(
        f"  Total publications in sources: {len(analysis_results['all_publications'])}"
    )
    click.echo(
        f"  Total publications in Zotero: {len(analysis_results['zotero_pubs'])}"
    )
    click.echo(f"  Missing from Zotero: {len(analysis_results['missing'])}")
    click.echo(f"  Duplicates in Zotero: {len(analysis_results['duplicates'])}")
    click.echo(
        f"  Potential matches to review: {len(analysis_results['potential_matches'])}"
    )


@click.group()
@click.version_option(version="0.1.0", prog_name="puby")
def cli() -> None:
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
) -> None:
    """Compare publications across sources and identify missing or duplicate entries."""
    _validate_sources(scholar, orcid, pure)

    client = PublicationClient(verbose=verbose)
    sources = _initialize_sources(scholar, orcid, pure)
    zotero_lib = _initialize_zotero(zotero, api_key)

    all_publications = _fetch_source_publications(client, sources, verbose)
    zotero_pubs = _fetch_zotero_publications(client, zotero_lib, verbose)

    analysis_results = _analyze_publications(all_publications, zotero_pubs)
    _report_results(analysis_results, format)


@cli.command()
@click.option(
    "--orcid",
    help="ORCID profile URL (e.g., https://orcid.org/0000-0000-0000-0000)",
    type=str,
)
@click.option(
    "--output",
    help="Output file path",
    type=str,
    default="publications.bib",
)
def fetch(orcid: Optional[str], output: str) -> None:
    """Fetch publications from a source and save to file."""

    if not orcid:
        click.echo("Error: --orcid is required for fetch command", err=True)
        sys.exit(1)

    client = PublicationClient()
    source = ORCIDSource(orcid)

    click.echo(f"Fetching publications from ORCID: {orcid}")
    publications = client.fetch_publications(source)

    click.echo(f"Found {len(publications)} publications")

    # Save to BibTeX file
    try:
        with open(output, 'w', encoding='utf-8') as f:
            for pub in publications:
                f.write(pub.to_bibtex())
                f.write('\n\n')
        click.echo(f"Successfully saved {len(publications)} publications to {output}")
    except Exception as e:
        click.echo(f"Error saving to {output}: {e}", err=True)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
