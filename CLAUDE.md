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
├── puby/                    # Main package
│   ├── __init__.py          # Package initialization  
│   ├── cli.py               # CLI entry point
│   ├── client.py            # Main client coordinator
│   ├── models.py            # Data models
│   ├── sources.py           # Source adapters
│   ├── matcher.py           # Publication matching
│   └── reporter.py          # Output formatting
├── tests/                   # Test suite
├── pyproject.toml           # Project configuration
├── README.md                # User documentation
└── DESIGN.md                # Technical documentation
```

## Dependencies
See pyproject.toml for complete dependency list. Main dependencies:
- **click**: CLI framework  
- **requests**: HTTP client
- **pyzotero**: Zotero API client
- **beautifulsoup4**: HTML parsing for Scholar/Pure
- **tabulate**: Table formatting
- **colorama**: Cross-platform colored output

## Code Quality Standards
- Black formatting (88 char line limit)
- Ruff linting with strict rules  
- Type hints with mypy checking
- Comprehensive error handling
- No hardcoded credentials or secrets