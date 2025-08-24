"""Command-line interface for puby."""

import click
from colorama import init as colorama_init

from .commands.check import check
from .commands.fetch import fetch

# Initialize colorama for cross-platform colored output
colorama_init()




@click.group()
@click.version_option(version="0.1.0", prog_name="puby")
def cli() -> None:
    """Puby - Publication list management tool for researchers."""
    pass


# Add commands to the CLI group
cli.add_command(check)
cli.add_command(fetch)




def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
