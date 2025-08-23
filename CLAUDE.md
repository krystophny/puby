# CLAUDE.md - puby Project Configuration

## Project Information
- **Name**: puby (Publication Management Tool)
- **Language**: Fortran 2018+ with ISO C bindings
- **Build System**: Fortran Package Manager (fpm)
- **Target**: Command-line publication list management and analysis

## Build Commands
```bash
# Build the project
fpm build

# Run tests
fpm test

# Run executable
fpm run puby

# Install development dependencies (libcurl-dev)
# Ubuntu/Debian: sudo apt install libcurl4-openssl-dev
# macOS: brew install curl
# Fedora/RHEL: sudo dnf install libcurl-devel
```

## Project Structure
```
puby/
├── app/
│   └── main.f90              # CLI entry point
├── src/
│   ├── puby.f90             # Main module
│   ├── puby_curl.f90        # libcurl ISO C bindings
│   ├── puby_http.f90        # High-level HTTP interface
│   ├── puby_types.f90       # Data structures
│   ├── puby_orcid.f90       # ORCID API client
│   ├── puby_zotero.f90      # Zotero API client
│   ├── puby_match.f90       # Publication matching
│   └── puby_report.f90      # Report generation
├── test/
│   └── test_*.f90           # Unit tests
├── fpm.toml                 # Build configuration
└── DESIGN.md                # Architecture documentation
```

## Dependencies
- **libcurl**: HTTP client library (system dependency)
- **json-fortran**: JSON parsing (if needed for complex responses)

## Development Notes
- Uses ISO C bindings for libcurl integration
- Memory-safe C/Fortran boundary management required
- Follow QADS principles: CORRECTNESS > PERFORMANCE > KISS > SRP
- Target <500 lines per module, <50 lines per function
- 88 character line limit, 4-space indentation

## API Integration Endpoints
- **ORCID API**: https://pub.orcid.org/v3.0/{orcid-id}/works
- **Zotero API**: https://api.zotero.org/groups/{group-id}/items
- **Web scraping**: Google Scholar, Pure (future enhancement)

## Testing Strategy
- Unit tests for each module
- Integration tests for API clients
- Mock HTTP responses for reliable testing
- Test data: Use Christopher Albert's public profiles

## Success Metrics (MVP)
- CLI can parse ORCID ID and Zotero group URL
- Successfully fetches publications from both sources
- Identifies and reports potential duplicates
- Suggests missing publications from ORCID not in Zotero
- Execution time under 30 seconds for typical researcher profile