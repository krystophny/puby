"""Utility functions for CLI commands."""

import os
import sys
from pathlib import Path
from typing import Optional

import click


def validate_file_writable(filepath: str) -> None:
    """Validate that a file path can be written to.
    
    Args:
        filepath: Path to validate for writeability
        
    Raises:
        SystemExit: If file cannot be written (prints error and exits)
    """
    try:
        # Convert to Path object for better path handling
        path = Path(filepath)
        
        # Check if parent directory exists and is writable
        parent_dir = path.parent
        if not parent_dir.exists():
            click.echo(
                f"Error: Directory does not exist: {parent_dir}", err=True
            )
            sys.exit(1)
        
        if not parent_dir.is_dir():
            click.echo(
                f"Error: Parent path is not a directory: {parent_dir}", err=True
            )
            sys.exit(1)
        
        if not os.access(parent_dir, os.W_OK):
            click.echo(
                f"Error: Permission denied - cannot write to directory: {parent_dir}",
                err=True,
            )
            sys.exit(1)
        
        # If file exists, check if it can be overwritten
        if path.exists():
            if not path.is_file():
                click.echo(
                    f"Error: Path exists but is not a file: {filepath}", err=True
                )
                sys.exit(1)
            if not os.access(path, os.W_OK):
                click.echo(
                    f"Error: Permission denied - cannot overwrite file: {filepath}",
                    err=True,
                )
                sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: Cannot validate file path {filepath}: {e}", err=True)
        sys.exit(1)


def validate_sources(
    scholar: Optional[str], orcid: Optional[str], pure: Optional[str]
) -> None:
    """Validate that at least one source is provided."""
    if not any([scholar, orcid, pure]):
        click.echo(
            "Error: At least one source URL (--scholar, --orcid, or --pure) is required.",
            err=True,
        )
        sys.exit(1)