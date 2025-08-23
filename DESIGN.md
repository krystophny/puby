# Puby - Technical Design Document

## Overview

Puby is a Python-based command-line tool for managing academic publication lists across multiple sources. It helps researchers identify missing publications, duplicates, and synchronization issues between their various academic profiles and reference management systems.

## Architecture

### Technology Stack

- **Language**: Python 3.8+
- **CLI Framework**: Click
- **HTTP Client**: requests
- **Zotero Integration**: pyzotero
- **Data Processing**: BeautifulSoup4 (for HTML parsing)
- **Output Formatting**: tabulate, built-in json/csv modules

### Module Structure

```
puby/
├── __init__.py       # Package initialization and exports
├── cli.py           # Command-line interface
├── client.py        # Main client coordinating operations
├── models.py        # Data models (Publication, Author)
├── sources.py       # Source adapters (ORCID, Scholar, Pure, Zotero)
├── matcher.py       # Publication matching algorithms
└── reporter.py      # Output formatting and reporting
```

### Core Components

#### 1. Data Models (`models.py`)

- **Publication**: Central data model representing a scientific publication
  - Attributes: title, authors, year, DOI, journal, etc.
  - Methods: `matches()`, `to_bibtex()`, similarity calculation
  
- **Author**: Represents publication authors
  - Attributes: name, given_name, family_name, ORCID, affiliation

#### 2. Source Adapters (`sources.py`)

Abstract base class `PublicationSource` with implementations:

- **ORCIDSource**: Fetches from ORCID API v3.0
  - Direct API access, no authentication required for public data
  - Parses work summaries and detailed work data
  
- **ScholarSource**: Google Scholar integration
  - Currently placeholder (scraping challenges)
  - Future: scholarly library integration
  
- **PureSource**: Institutional Pure portals
  - Institution-specific implementation required
  
- **ZoteroLibrary**: Zotero library access
  - Uses pyzotero for API interaction
  - Supports both public and private libraries

#### 3. Matching Engine (`matcher.py`)

- **PublicationMatcher**: Handles publication comparison
  - DOI-based exact matching
  - Title similarity using Jaccard coefficient
  - Fuzzy matching with configurable thresholds
  - Duplicate detection within collections

#### 4. CLI Interface (`cli.py`)

- Built with Click for robust command parsing
- Commands:
  - `check`: Main comparison command
  - `fetch`: Direct fetching from sources (future)
- Comprehensive error handling and validation

#### 5. Reporting (`reporter.py`)

- Multiple output formats:
  - Table (human-readable)
  - JSON (machine-readable)
  - CSV (spreadsheet-compatible)
  - BibTeX (reference manager import)

## Data Flow

1. **Input**: User provides source URLs and Zotero library ID
2. **Fetching**: Each source adapter fetches publications
3. **Normalization**: Publications converted to common model
4. **Matching**: Publications compared using matching algorithms
5. **Analysis**: Missing, duplicates, and potential matches identified
6. **Output**: Results formatted and displayed

## API Integration

### ORCID API

- Base URL: `https://pub.orcid.org/v3.0`
- No authentication required for public data
- Endpoints used:
  - `/{orcid-id}/works`: List of works
  - `/{orcid-id}/work/{put-code}`: Detailed work data

### Zotero API

- Uses pyzotero library for abstraction
- Supports API key authentication
- Fetches all items with `everything(top())`

## Matching Algorithm

### Similarity Calculation

1. **DOI Matching** (weight: 1.0)
   - Exact match = 100% similarity
   - Different DOIs = 0% similarity

2. **Title Similarity** (weight: 0.7)
   - Jaccard similarity on word sets
   - Case-insensitive comparison

3. **Year Matching** (weight: 0.2)
   - Binary match (same year or not)

4. **Author Matching** (weight: 0.1)
   - First author comparison
   - Future: full author list comparison

### Thresholds

- **Exact Match**: ≥ 0.8 similarity
- **Potential Match**: 0.5 - 0.8 similarity
- **No Match**: < 0.5 similarity

## Error Handling

- Network errors: Graceful degradation with logging
- API errors: User-friendly error messages
- Invalid input: Validation at CLI level
- Missing data: Optional fields handled gracefully

## Performance Considerations

- Asynchronous fetching: Future optimization for multiple sources
- Caching: Potential for local caching of API responses
- Batch processing: Handle large publication lists efficiently

## Security

- No credentials stored locally
- API keys passed as command-line arguments or environment variables
- HTTPS enforced for all API communications
- No sensitive data logging

## Testing Strategy

- Unit tests for each module
- Integration tests for API interactions
- Mock responses for reliable testing
- CLI command testing with Click's testing utilities

## Current Implementation Status

### Completed Features ✅
- CLI argument parsing with comprehensive help
- ORCID API integration and publication fetching
- Zotero API integration (public and private libraries)
- Google Scholar profile scraping
- Pure research portal support (API and HTML fallback)
- Publication matching algorithms with configurable thresholds
- Multiple output formats (table, JSON, CSV, BibTeX)
- Duplicate detection within libraries
- Missing publication identification
- Cross-platform colored console output

## Development Workflow

1. **Setup**: Virtual environment with pip
2. **Dependencies**: Managed via pyproject.toml
3. **Testing**: pytest with coverage
4. **Linting**: black + ruff
5. **Type Checking**: mypy
6. **Documentation**: Docstrings + README

## Deployment

- **Package Distribution**: PyPI
- **Installation**: pip install
- **Updates**: Semantic versioning
- **Compatibility**: Python 3.8+

## Success Metrics

- **Accuracy**: > 95% correct matching
- **Performance**: < 30s for typical researcher profile
- **Reliability**: Graceful handling of API failures
- **Usability**: Intuitive CLI with helpful error messages