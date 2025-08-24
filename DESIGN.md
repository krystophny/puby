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
├── models.py        # Data models (Publication, Author, ZoteroConfig)
├── sources.py       # Abstract base class for publication sources
├── orcid_source.py  # ORCID API implementation
├── scholar_source.py # Google Scholar scraper
├── pure_source.py   # Pure portal integration (API + HTML fallback)
├── zotero_source.py # Modern Zotero source with user/group support
├── legacy_sources.py # Legacy Zotero implementation
├── matcher.py       # Publication matching algorithms
├── reporter.py      # Output formatting and reporting
├── bibtex_parser.py # BibTeX parsing utilities
├── env.py          # Environment variable support
└── base.py         # Base utilities and common functionality
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
  
- **ScholarSource**: Google Scholar profile scraping
  - Web scraping with rate limiting
  - Robust parsing of publication lists with pagination
  - User-Agent rotation and anti-blocking measures
  
- **PureSource**: Pure research portals with API fallback
  - Primary: REST API access for structured data
  - Fallback: HTML scraping when API unavailable
  - Support for multiple Pure portal configurations
  
- **ZoteroSource**: Modern Zotero integration
  - User and group library support
  - Automatic user ID discovery from API key
  - "My Publications" endpoint for authored works
  - Multiple output formats (JSON, BibTeX)
  - Connection validation and error handling
  
- **ZoteroLibrary**: Legacy Zotero implementation (deprecated)
  - Maintained for backward compatibility
  - Basic pyzotero wrapper

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
  - Table (human-readable with colors)
  - JSON (machine-readable)
  - CSV (spreadsheet-compatible)
  - BibTeX (reference manager import)
- Analysis reporting with statistics
- Sync recommendations
- Missing publication export functionality

## Data Flow

1. **Input**: User provides source URLs and Zotero library ID
2. **Fetching**: Each source adapter fetches publications
3. **Normalization**: Publications converted to common model
4. **Matching**: Publications compared using matching algorithms
5. **Analysis**: Missing, duplicates, and potential matches identified
6. **Output**: Results formatted and displayed

## API Integration

### ORCID API v3.0

- Base URL: `https://pub.orcid.org/v3.0`
- Public access (no authentication required)
- Endpoints:
  - `/{orcid-id}/works`: Work summaries list
  - `/{orcid-id}/work/{put-code}`: Detailed work data
- Rate limiting: 12 requests per second
- Comprehensive error handling for API failures

### Zotero Web API

- User libraries: Auto-discovery via `/users/current` with API key
- Group libraries: Direct access via group ID
- My Publications: `/users/{user-id}/publications` (authored works)
- Formats: JSON (structured) and BibTeX (direct export)
- Connection validation before data fetching
- Proper error handling for authentication failures

### Google Scholar

- Web scraping with respectful rate limiting (2-second delays)
- Profile URL parsing: `citations?user={id}`
- Pagination support via `start` parameter
- Anti-blocking: User-Agent rotation and delay patterns

### Pure Research Portals

- Primary: REST API at `/ws/api/persons/{id}/research-outputs`
- Fallback: HTML scraping with JSON-LD metadata extraction
- Institution-specific URL pattern recognition
- Rate limiting: 3-second delays for institutional servers

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

## Performance

- **Rate Limiting**: Source-specific delays to prevent API throttling
- **Efficient Matching**: DOI-based exact matching before expensive similarity calculations
- **Pagination Support**: Handle large publication lists across all sources
- **Memory Efficient**: Stream processing for large datasets
- **Fast Similarity**: Optimized Jaccard coefficient for title matching
- **Connection Validation**: Early failure detection to avoid unnecessary processing

## Security and Configuration

- **No Local Storage**: API keys never cached or stored locally
- **Multi-tier Configuration**: Command line > environment > .env file
- **HTTPS Enforcement**: All API communications use secure protocols
- **API Key Validation**: Early validation with clear error messages
- **No Silent Failures**: All authentication errors reported with remediation steps
- **Honest Implementation**: No fake functionality when API keys missing

## Testing Strategy

- Unit tests for each module
- Integration tests for API interactions
- Mock responses for reliable testing
- CLI command testing with Click's testing utilities

## Implementation Features

### Core Functionality ✅
- **CLI Interface**: Comprehensive argument parsing with help documentation
- **ORCID Integration**: Full API v3.0 implementation with work details
- **Google Scholar**: Profile scraping with pagination and rate limiting
- **Pure Portals**: API-first approach with HTML fallback support
- **Zotero Libraries**: User/group libraries, auto-discovery, My Publications endpoint
- **Publication Matching**: DOI-based exact matching plus fuzzy title matching
- **Output Formats**: Table, JSON, CSV, BibTeX with colored console output
- **BibTeX Export**: Missing publications export with citation key conflict resolution
- **Environment Support**: .env file support for API key management
- **Error Handling**: Honest API key validation with actionable error messages
- **Testing**: 229 comprehensive tests covering all components

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