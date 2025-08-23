# Puby - Publication List Management Tool

A Python tool for researchers to manage and synchronize their publication lists across multiple sources.

## Features

- 📚 Fetch publications from multiple sources (ORCID, Google Scholar, Pure portals)
- 🔄 Synchronize with Zotero libraries
- 🔍 Identify missing publications and duplicates
- 📊 Multiple output formats (table, JSON, CSV, BibTeX)
- 🎨 Clean command-line interface with colored output
- 🚀 Fast and efficient publication matching

## Installation

```bash
pip install puby
```

Or install from source:

```bash
git clone https://github.com/krystophny/puby.git
cd puby
pip install -e .
```

## Quick Start

### Basic Usage

Compare your ORCID publications with your Zotero library:

```bash
puby check --orcid https://orcid.org/0000-0003-4773-416X --zotero 12345
```

### Multiple Sources

Check publications from multiple sources:

```bash
puby check \
  --scholar https://scholar.google.com/citations?user=ABC123 \
  --orcid https://orcid.org/0000-0003-4773-416X \
  --pure https://pure.university.edu/person/john-doe \
  --zotero 12345 \
  --api-key YOUR_ZOTERO_API_KEY
```

### Output Formats

Export results in different formats:

```bash
# Table format (default)
puby check --orcid https://orcid.org/0000-0003-4773-416X --zotero 12345

# JSON format
puby check --orcid https://orcid.org/0000-0003-4773-416X --zotero 12345 --format json

# CSV format
puby check --orcid https://orcid.org/0000-0003-4773-416X --zotero 12345 --format csv

# BibTeX format
puby check --orcid https://orcid.org/0000-0003-4773-416X --zotero 12345 --format bibtex
```

## Command Line Options

### `puby check`

Compare publications across sources and identify missing or duplicate entries.

| Option | Description | Required |
|--------|-------------|----------|
| `--scholar URL` | Google Scholar profile URL | No |
| `--orcid URL` | ORCID profile URL | No |
| `--pure URL` | Pure research portal URL | No |
| `--zotero ID` | Zotero group or library ID | Yes |
| `--api-key KEY` | Zotero API key (for private libraries) | No |
| `--format FORMAT` | Output format: table, json, csv, bibtex | No |
| `--verbose` | Enable verbose output | No |

**Note**: At least one source URL (--scholar, --orcid, or --pure) must be provided.

## Configuration

### Zotero API Key

To access private Zotero libraries, you'll need an API key:

1. Log in to [Zotero](https://www.zotero.org)
2. Go to Settings → Feeds/API
3. Create a new API key with read permissions
4. Use the key with `--api-key` option

### Environment Variables

You can set default values using environment variables:

```bash
export PUBY_ZOTERO_API_KEY=your_api_key
export PUBY_ZOTERO_LIBRARY=your_library_id
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

## Architecture

Puby uses a modular architecture with clear separation of concerns:

- **CLI** (`cli.py`): Command-line interface using Click
- **Models** (`models.py`): Data models for publications and authors
- **Sources** (`sources.py`): Adapters for different publication sources
- **Matcher** (`matcher.py`): Publication matching and comparison logic
- **Reporter** (`reporter.py`): Output formatting and reporting
- **Client** (`client.py`): Main client coordinating operations

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
- Check the [documentation](https://github.com/krystophny/puby/wiki)

## Roadmap

- [ ] Google Scholar integration (via scholarly library)
- [ ] Pure portal API support (institution-specific)
- [ ] Automatic duplicate merging
- [ ] Publication metadata enhancement
- [ ] Web interface
- [ ] Batch operations support
- [ ] Export to multiple formats simultaneously
- [ ] Citation count tracking