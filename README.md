# Puby - Publication List Management Tool

A Python command-line tool for researchers to manage and synchronize their publication lists across multiple academic sources.

## Features

- Fetch publications from ORCID, Google Scholar, and Pure research portals
- Compare with Zotero personal or group libraries
- Identify missing publications and duplicates
- Export missing publications to BibTeX
- Multiple output formats (table, JSON, CSV, BibTeX)
- User and group library support with auto-discovery
- Environment variable configuration
- Colored console output with verbose mode

## Installation

**Currently in development - install from source:**

```bash
git clone https://github.com/krystophny/puby.git
cd puby
pip install -e .
```

## Quick Start

### 1. Set up Zotero API Key

```bash
# Create .env file in your project directory
echo "ZOTERO_API_KEY=your_api_key_here" > .env
```

### 2. Basic Usage

Compare ORCID publications with your personal Zotero library:

```bash
# Auto-discover your user library
puby check --orcid https://orcid.org/0000-0003-4773-416X --zotero-library-type user
```

### 3. Multiple Sources

Check publications from multiple academic sources:

```bash
puby check \
  --scholar "https://scholar.google.com/citations?user=ABC123" \
  --orcid https://orcid.org/0000-0003-4773-416X \
  --pure https://pure.university.edu/person/john-doe \
  --zotero-library-type user
```

### 4. Export Missing Publications

```bash
# Export missing publications to BibTeX file
puby check \
  --orcid https://orcid.org/0000-0003-4773-416X \
  --zotero-library-type user \
  --export-missing missing.bib
```

### 5. Group Libraries and Advanced Features

```bash
# Compare with group library
puby check \
  --orcid https://orcid.org/0000-0003-4773-416X \
  --zotero 12345 \
  --zotero-library-type group

# Use Zotero "My Publications" endpoint (user libraries only)
puby check \
  --orcid https://orcid.org/0000-0003-4773-416X \
  --zotero-library-type user \
  --zotero-my-publications
```

## Configuration

### API Key Setup

1. Get your Zotero API key from [Zotero Settings](https://www.zotero.org/settings/keys)
2. Set up authentication:

```bash
# Option 1: Environment file (.env)
echo "ZOTERO_API_KEY=your_api_key" > .env

# Option 2: Environment variable
export ZOTERO_API_KEY=your_api_key

# Option 3: Command line (overrides above)
puby check --api-key your_api_key ...
```

## Commands

### `puby check` - Compare Publications

**Required:** At least one source URL (--scholar, --orcid, or --pure)

**Source Options:**
- `--scholar URL` - Google Scholar profile URL
- `--orcid URL` - ORCID profile URL  
- `--pure URL` - Pure research portal URL

**Zotero Options:**
- `--zotero ID` - Group ID (for group libraries) or User ID (optional for user libraries)
- `--zotero-library-type [group|user]` - Library type (default: group)
- `--zotero-my-publications` - Use My Publications endpoint (user libraries only)
- `--zotero-format [json|bibtex]` - My Publications format (default: json)
- `--api-key KEY` - API key (overrides environment)

**Output Options:**
- `--format [table|json|csv|bibtex]` - Output format (default: table)
- `--export-missing [FILE]` - Export missing publications to BibTeX
- `--verbose` - Detailed progress information

### `puby fetch` - Export Single Source

Fetch publications from ORCID and save to BibTeX file:

```bash
# Basic usage
puby fetch --orcid https://orcid.org/0000-0003-4773-416X

# Custom output file
puby fetch --orcid https://orcid.org/0000-0003-4773-416X --output my_pubs.bib
```

**Options:**
- `--orcid URL` - ORCID profile URL (required)
- `--output FILE` - Output file path (default: publications.bib)

## Examples

```bash
# Compare ORCID with personal Zotero library
puby check --orcid https://orcid.org/0000-0003-4773-416X --zotero-library-type user

# Multiple sources with group library
puby check \
  --orcid https://orcid.org/0000-0003-4773-416X \
  --scholar "https://scholar.google.com/citations?user=ABC123" \
  --zotero 12345 \
  --zotero-library-type group

# Export missing publications and show detailed output
puby check \
  --orcid https://orcid.org/0000-0003-4773-416X \
  --zotero-library-type user \
  --export-missing missing.bib \
  --verbose

# Use My Publications endpoint with BibTeX format
puby check \
  --orcid https://orcid.org/0000-0003-4773-416X \
  --zotero-library-type user \
  --zotero-my-publications \
  --zotero-format bibtex
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/krystophny/puby.git
cd puby

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=puby

# Run specific test file
pytest tests/test_matcher.py
```

### Code Quality

```bash
# Format code
black puby tests

# Lint code
ruff check puby tests

# Type checking
mypy puby
```

For detailed architecture information, see [DESIGN.md](DESIGN.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for the CLI
- Uses [pyzotero](https://github.com/urschrei/pyzotero) for Zotero integration
- ORCID API for publication data
- Community contributors

## Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/krystophny/puby/issues)

