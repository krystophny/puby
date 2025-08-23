# Puby - Publication List Management Tool

## MVP Architecture

### Vision
A command-line tool that helps researchers maintain up-to-date publication lists by integrating multiple sources (Google Scholar, ORCID, Pure) with Zotero API validation.

### Core MVP Components

```
puby CLI
├── Input Sources
│   ├── URL Parser (Scholar, ORCID, Pure)
│   ├── BibTeX Scraper
│   └── Data Normalizer
├── Zotero Integration
│   ├── API Client
│   ├── Publication Matcher
│   └── Duplicate Detector
├── Analysis Engine
│   ├── Missing Publication Detector
│   ├── Duplicate Identifier
│   └── Data Quality Checker
└── Output Generator
    ├── Missing Publications Report
    ├── Duplicate Report
    └── Sync Recommendations
```

### MVP User Flow
1. User provides URLs: `puby check --scholar=URL --orcid=URL --pure=URL --zotero=GROUP`
2. Tool scrapes publications from each source
3. Tool queries Zotero API for existing publications
4. Tool analyzes differences and generates reports
5. Tool outputs actionable recommendations

### Technical Architecture

#### Language: Modern Fortran (2018+)
- **Rationale**: Existing fpm project, excellent for data processing
- **HTTP Client**: Use system calls to curl/wget for MVP
- **JSON Parsing**: Custom lightweight parser for API responses
- **String Processing**: Native Fortran string handling

#### Module Structure
```fortran
src/
├── puby.f90                    ! Main module with public API
├── puby_types.f90             ! Type definitions
├── puby_http.f90              ! HTTP client wrapper
├── puby_parsers.f90           ! URL/content parsers
├── puby_zotero.f90            ! Zotero API integration
├── puby_analysis.f90          ! Publication analysis
└── puby_reports.f90           ! Output generation
```

#### Core Types
```fortran
type :: publication_t
    character(len=:), allocatable :: title
    character(len=:), allocatable :: authors
    character(len=:), allocatable :: journal
    character(len=:), allocatable :: year
    character(len=:), allocatable :: doi
    character(len=:), allocatable :: url
    character(len=:), allocatable :: source
end type

type :: zotero_config_t
    character(len=:), allocatable :: api_key
    character(len=:), allocatable :: group_id
    character(len=:), allocatable :: library_type
end type
```

### MVP Workflow

#### Phase 1: Basic CLI Framework
- Argument parsing for URLs and Zotero config
- Basic HTTP wrapper around system curl
- Simple text output

#### Phase 2: Data Extraction
- Google Scholar HTML parsing
- ORCID API integration
- Pure API/scraping
- Basic publication data structure

#### Phase 3: Zotero Integration
- Zotero API client
- Publication retrieval
- Basic matching algorithm (title/DOI comparison)

#### Phase 4: Analysis & Reporting
- Missing publication detection
- Duplicate identification
- Formatted text reports

### Integration Points

#### External Dependencies
- **curl/wget**: HTTP requests (system calls)
- **Claude CLI**: Future AI-assisted text processing
- **Zotero API**: Publication validation and sync

#### API Integrations
1. **Zotero API v3**: Group/library access
2. **ORCID Public API**: Publication retrieval
3. **Web Scraping**: Google Scholar, Pure (as needed)

### MVP Constraints

#### What's IN MVP
- Single command execution
- Text-based configuration
- Simple console output
- Basic duplicate detection (title/DOI matching)
- Support for 1-2 URL sources initially

#### What's OUT of MVP
- Interactive configuration
- GUI interface
- Complex fuzzy matching algorithms
- Automatic synchronization
- Publication editing features
- Bibliography generation
- Multi-user support

### Success Metrics
1. **Functional**: Can parse at least one URL source and detect basic mismatches with Zotero
2. **Performance**: Processes typical researcher profile (50-100 publications) in <30 seconds
3. **Usability**: Single command execution with clear output
4. **Reliability**: Handles network failures gracefully

### Risk Mitigation

#### Technical Risks
- **Web scraping fragility**: Start with stable APIs (ORCID), add scraping incrementally
- **HTTP complexity in Fortran**: Use system calls to mature tools (curl)
- **JSON parsing**: Implement minimal parser for needed fields only

#### Scope Risks
- **Feature creep**: Strict MVP focus, defer advanced matching algorithms
- **Perfect matching**: Accept simple heuristics initially
- **Universal source support**: Start with 1-2 sources, expand later

### Development Priority

1. **Core CLI framework** (args, config, basic flow)
2. **HTTP client wrapper** (curl system calls)
3. **Single URL source parser** (ORCID API - most structured)
4. **Basic Zotero integration** (retrieve publications)
5. **Simple analysis** (exact title/DOI matching)
6. **Text report generation**
7. **Additional source support** (Scholar, Pure)

### Future Enhancements (Post-MVP)
- Fuzzy publication matching using Claude CLI
- Interactive publication review mode
- Configuration file support
- Batch processing multiple researchers
- Integration with reference managers beyond Zotero
- Publication impact metrics
- Citation network analysis

This MVP design prioritizes rapid delivery of core functionality while establishing a solid foundation for future enhancements.