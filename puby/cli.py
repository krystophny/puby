"""Command-line interface for puby."""

import sys
from typing import List, Optional

import click
from colorama import init as colorama_init

from .client import PublicationClient
from .env import get_api_key
from .legacy_sources import ZoteroLibrary
from .matcher import PublicationMatcher
from .models import Publication, ZoteroConfig
from .reporter import ConsoleReporter
from .sources import (
    ORCIDSource,
    PublicationSource,
    PureSource,
    ScholarSource,
    ZoteroSource,
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


def _initialize_zotero_source(
    zotero: Optional[str],
    library_type: str,
    api_key: Optional[str],
    use_my_publications: bool = False,
    format: str = "json",
) -> ZoteroSource:
    """Initialize modern ZoteroSource with error handling."""
    try:
        # Create ZoteroConfig
        config = ZoteroConfig(
            api_key=api_key or "",
            group_id=zotero,  # Can be None for user libraries (auto-discovery)
            library_type=library_type,
            use_my_publications=use_my_publications,
            format=format,
        )

        return ZoteroSource(config)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nTo fix this issue:", err=True)
        click.echo(
            "1. Get your Zotero API key from: https://www.zotero.org/settings/keys",
            err=True,
        )
        if library_type == "user":
            click.echo(
                "2. For user libraries, you can omit --zotero and let the system auto-discover your user ID",
                err=True,
            )
            click.echo(
                "   OR provide your user ID with --zotero YOUR_USER_ID", err=True
            )
            if use_my_publications:
                click.echo(
                    "3. My Publications endpoint is only available for user libraries",
                    err=True,
                )
        else:
            click.echo(
                "2. For group libraries, provide the group ID with --zotero GROUP_ID",
                err=True,
            )
            if use_my_publications:
                click.echo(
                    "3. My Publications endpoint is not available for group libraries",
                    err=True,
                )
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
    client: PublicationClient, zotero_source: ZoteroSource, verbose: bool
) -> List[Publication]:
    """Fetch publications from Zotero library using ZoteroSource."""
    if verbose:
        library_type = zotero_source.config.library_type
        library_id = zotero_source.config.group_id or "auto-discovered"
        click.echo(f"  Fetching from Zotero {library_type} library ({library_id})...")
    try:
        zotero_pubs = client.fetch_publications(zotero_source)
        if verbose:
            click.echo(f"    Found {len(zotero_pubs)} publications")
        return zotero_pubs
    except ValueError as e:
        # Propagate authentication errors with clear messages
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            click.echo(f"Error: {e}", err=True)
            click.echo("\nTo fix this issue:", err=True)
            click.echo(
                "1. Get your Zotero API key from: https://www.zotero.org/settings/keys",
                err=True,
            )
            click.echo("2. Run the command again with --api-key YOUR_KEY", err=True)
            sys.exit(1)
        raise


def _export_missing_publications(
    missing_publications: List[Publication], filename: Optional[str]
) -> None:
    """Export missing publications to BibTeX file."""
    if filename is None:
        filename = "missing_publications.bib"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            # Write header comment
            f.write("% BibTeX export of missing publications\n")
            f.write("% Generated by puby\n")
            f.write(f"% Total entries: {len(missing_publications)}\n")
            f.write("\n")

            if not missing_publications:
                f.write("% No missing publications found\n")
                return

            # Collect all citation keys to resolve conflicts
            existing_keys = []
            resolved_publications = []

            for pub in missing_publications:
                resolved_key = pub.resolve_key_conflicts(existing_keys)
                existing_keys.append(resolved_key)
                resolved_publications.append((pub, resolved_key))

            # Write BibTeX entries with resolved keys
            for pub, resolved_key in resolved_publications:
                bibtex_entry = pub.to_bibtex()
                # Replace the original key with resolved key
                original_key = pub.generate_citation_key()
                bibtex_entry = bibtex_entry.replace(
                    f"@article{{{original_key},", f"@article{{{resolved_key},", 1
                )
                f.write(bibtex_entry)
                f.write("\n\n")

    except PermissionError as e:
        raise PermissionError(f"Permission denied writing to {filename}") from e
    except Exception as e:
        raise Exception(f"Error writing to {filename}: {e}") from e


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
    help="Zotero group ID or user library ID (optional for user libraries with auto-discovery)",
    type=str,
)
@click.option(
    "--api-key",
    help="Zotero API key (required for private libraries)",
    type=str,
)
@click.option(
    "--zotero-library-type",
    type=click.Choice(["group", "user"]),
    default="group",
    help="Zotero library type (group or user library, defaults to group for backward compatibility)",
)
@click.option(
    "--zotero-my-publications",
    is_flag=True,
    help="Use Zotero My Publications endpoint (user libraries only, returns authored publications)",
)
@click.option(
    "--zotero-format",
    type=click.Choice(["json", "bibtex"]),
    default="json",
    help="Format for Zotero My Publications endpoint (json or bibtex)",
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
@click.option(
    "--export-missing",
    help="Export missing publications to BibTeX file",
    type=str,
    metavar="[FILENAME]",
    default=None,
    required=False,
)
def check(
    scholar: Optional[str],
    orcid: Optional[str],
    pure: Optional[str],
    zotero: Optional[str],
    api_key: Optional[str],
    zotero_library_type: str,
    zotero_my_publications: bool,
    zotero_format: str,
    format: str,
    verbose: bool,
    export_missing: Optional[str],
) -> None:
    """Compare publications across sources and identify missing or duplicate entries."""
    _validate_sources(scholar, orcid, pure)

    # Validate Zotero configuration
    if zotero_library_type == "group" and not zotero:
        click.echo("Error: --zotero is required for group library type.", err=True)
        sys.exit(1)

    # Validate My Publications configuration
    if zotero_my_publications and zotero_library_type == "group":
        click.echo(
            "Error: --zotero-my-publications is only supported for user libraries (--zotero-library-type user).",
            err=True,
        )
        sys.exit(1)

    # Get API key with proper precedence (CLI > env > .env)
    resolved_api_key = get_api_key(api_key)

    client = PublicationClient(verbose=verbose)
    sources = _initialize_sources(scholar, orcid, pure)
    zotero_source = _initialize_zotero_source(
        zotero,
        zotero_library_type,
        resolved_api_key,
        zotero_my_publications,
        zotero_format,
    )

    all_publications = _fetch_source_publications(client, sources, verbose)
    zotero_pubs = _fetch_zotero_publications(client, zotero_source, verbose)

    analysis_results = _analyze_publications(all_publications, zotero_pubs)

    # Export missing publications if requested
    if export_missing is not None:
        missing_pubs = analysis_results["missing"]
        try:
            _export_missing_publications(missing_pubs, export_missing)
            click.echo(
                f"Exported {len(missing_pubs)} missing publications to {export_missing}"
            )
        except Exception as e:
            click.echo(f"Error exporting missing publications: {e}", err=True)
            sys.exit(1)

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
    
    # URL validation consistent with check command
    if "orcid.org" not in orcid:
        click.echo(f"Error: Invalid ORCID URL: {orcid}", err=True)
        sys.exit(1)
    
    # Initialize source with error handling consistent with check command
    try:
        source = ORCIDSource(orcid)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"Fetching publications from ORCID: {orcid}")
    
    # Fetch publications with consistent error handling
    try:
        publications = client.fetch_publications(source)
    except ValueError as e:
        # Handle authentication and validation errors with clean messages
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        # Handle all other errors (network, parsing, etc.)
        click.echo(f"Error fetching publications: {e}", err=True)
        sys.exit(1)

    click.echo(f"Found {len(publications)} publications")

    # Save to BibTeX file
    try:
        with open(output, "w", encoding="utf-8") as f:
            for pub in publications:
                f.write(pub.to_bibtex())
                f.write("\n\n")
        click.echo(f"Successfully saved {len(publications)} publications to {output}")
    except Exception as e:
        click.echo(f"Error saving to {output}: {e}", err=True)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
