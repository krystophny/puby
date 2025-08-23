# CLAUDE.md - puby Project Configuration

## Project Information
- **Name**: puby (Publication Management Tool)
- **Language**: Python 3.8+
- **Package Manager**: pip / poetry
- **Target**: Command-line publication list management and analysis

## Build Commands
```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=puby --cov-report=term-missing

# Format code
black puby tests

# Lint code  
ruff check puby tests

# Type checking
mypy puby

# Build package
python -m build

# Install from PyPI (when published)
pip install puby
```

## Project Structure
```
puby/
├── puby/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # CLI entry point with Click
│   ├── client.py            # Main client coordinator
│   ├── models.py            # Data models (Publication, Author)
│   ├── sources.py           # Source adapters (ORCID, Zotero, etc.)
│   ├── matcher.py           # Publication matching algorithms
│   └── reporter.py          # Output formatting
├── tests/
│   ├── test_cli.py          # CLI tests
│   ├── test_matcher.py      # Matching algorithm tests
│   ├── test_models.py       # Model tests
│   └── test_sources.py      # Source adapter tests
├── pyproject.toml           # Project configuration
├── README.md                # User documentation
└── DESIGN.md                # Architecture documentation
```

## Dependencies
- **click**: CLI framework
- **requests**: HTTP client
- **pyzotero**: Zotero API client
- **beautifulsoup4**: HTML parsing
- **tabulate**: Table formatting
- **colorama**: Cross-platform colored output

## Development Notes
- Uses Click for elegant CLI design
- Type hints throughout for better IDE support
- Follows PEP 8 with black formatting
- Comprehensive error handling
- Modular architecture for easy extension

## API Integration Endpoints
- **ORCID API**: https://pub.orcid.org/v3.0/{orcid-id}/works
- **Zotero API**: https://api.zotero.org/groups/{group-id}/items
- **Google Scholar**: Future enhancement via scholarly library
- **Pure portals**: Institution-specific APIs

## Testing Strategy
- Unit tests for each module with pytest
- Integration tests for API clients with responses mock
- CLI tests using Click's testing utilities
- Mock HTTP responses for reliable testing
- Coverage target: > 80%

## Success Metrics (MVP)
- CLI can parse arguments and validate input
- Successfully fetches publications from ORCID
- Connects to Zotero library (public or private)
- Identifies missing publications and duplicates
- Supports multiple output formats (table, JSON, CSV, BibTeX)
- Execution time under 30 seconds for typical profile

## Code Quality Standards
- Black formatting (88 char line limit)
- Ruff linting with strict rules
- Type hints with mypy checking
- Docstrings for all public functions
- No hardcoded credentials or secrets
- Comprehensive error messages