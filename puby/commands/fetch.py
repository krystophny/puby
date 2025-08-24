"""Fetch command implementation for downloading publications from ORCID."""

import sys
from typing import Optional

import click

from ..client import PublicationClient
from ..sources import ORCIDSource
from .utils import validate_file_writable


@click.command()
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
    """Fetch publications from ORCID and save to BibTeX file."""

    if not orcid:
        click.echo("Error: --orcid is required", err=True)
        sys.exit(1)

    # Validate output file writeability before making any API calls
    validate_file_writable(output)

    client = PublicationClient()
    
    # URL validation consistent with check command
    if "orcid.org" not in orcid.lower():
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