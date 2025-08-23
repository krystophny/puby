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

#### libcurl Integration Strategy

Based on patterns from the fortran-curl project, puby will use direct libcurl integration:

**ISO C Binding Approach**:
- Use `iso_c_binding` module for direct C library interfacing
- Create thin Fortran wrappers around essential libcurl functions:
  - `curl_easy_init()` - Initialize curl handle
  - `curl_easy_setopt()` - Configure request options
  - `curl_easy_perform()` - Execute HTTP request
  - `curl_easy_cleanup()` - Clean up resources
- Handle C string conversion and memory management carefully

**Key libcurl Functions Required**:
```fortran
! Core curl interface bindings
interface
    function curl_easy_init() bind(c, name='curl_easy_init')
        import :: c_ptr
        type(c_ptr) :: curl_easy_init
    end function
    
    function curl_easy_setopt(curl, option, parameter) bind(c, name='curl_easy_setopt')
        import :: c_ptr, c_int, c_long
        type(c_ptr), value :: curl
        integer(c_int), value :: option
        type(*), intent(in) :: parameter
        integer(c_int) :: curl_easy_setopt
    end function
    
    function curl_easy_perform(curl) bind(c, name='curl_easy_perform')
        import :: c_ptr, c_int
        type(c_ptr), value :: curl
        integer(c_int) :: curl_easy_perform
    end function
end interface
```

**Memory Management**:
- Use Fortran allocatable strings for HTTP response data
- Implement C callback functions to capture response body and headers
- Ensure proper cleanup of curl handles and allocated memory

#### Language: Modern Fortran (2018+)
- **Rationale**: Existing fpm project, excellent for data processing
- **HTTP Client**: Direct libcurl integration via ISO C bindings
- **JSON Parsing**: Custom lightweight parser for API responses
- **String Processing**: Native Fortran string handling

#### Module Structure
```fortran
src/
├── puby.f90                    ! Main module with public API
├── puby_curl.f90              ! libcurl ISO C bindings wrapper (IMPLEMENTED)
│   ├── Core libcurl interfaces (init, setopt, perform, cleanup) ✓
│   ├── C callback functions for response capture ✓
│   ├── C string conversion utilities ✓
│   └── Memory management for C/Fortran boundary ✓
├── puby_http.f90              ! High-level HTTP client interface (IMPLEMENTED)
│   ├── Simplified GET/POST wrappers ✓
│   ├── Response parsing and error handling ✓
│   ├── Configuration management (timeouts, SSL, headers) ✓
│   └── Fortran-native interface over libcurl bindings ✓
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

type :: http_response_t
    integer :: status_code
    character(len=:), allocatable :: body
    character(len=:), allocatable :: headers
    logical :: success
    character(len=256) :: error_message
end type

type :: http_config_t
    character(len=:), allocatable :: user_agent
    integer :: timeout_seconds
    logical :: follow_redirects
    logical :: verify_ssl
    logical :: initialized
end type
```

### MVP Workflow

#### Phase 1: Basic CLI Framework ✓
- Argument parsing for URLs and Zotero config ✓
- libcurl ISO C bindings setup with basic wrapper ✓
- Simple text output

#### Phase 2: HTTP Foundation ✓
- libcurl ISO C bindings module (`puby_curl.f90`) ✓
- High-level HTTP client interface (`puby_http.f90`) ✓
- GET/POST request functionality ✓
- Configuration and error handling ✓

#### Phase 3: Data Extraction (NEXT)
- Google Scholar HTML parsing
- ORCID API integration
- Pure API/scraping
- Basic publication data structure

#### Phase 4: Zotero Integration
- Zotero API client
- Publication retrieval
- Basic matching algorithm (title/DOI comparison)

#### Phase 5: Analysis & Reporting
- Missing publication detection
- Duplicate identification
- Formatted text reports

### Integration Points

#### External Dependencies
- **libcurl**: Direct HTTP client library integration
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
- **libcurl ISO C binding complexity**: Use proven patterns from fortran-curl project
- **Memory management in C interop**: Careful handling of allocatable strings and cleanup
- **JSON parsing**: Implement minimal parser for needed fields only

#### Scope Risks
- **Feature creep**: Strict MVP focus, defer advanced matching algorithms
- **Perfect matching**: Accept simple heuristics initially
- **Universal source support**: Start with 1-2 sources, expand later

### Development Priority

1. **Core CLI framework** (args, config, basic flow)
2. **libcurl ISO C bindings** (direct library integration)
3. **HTTP client wrapper** (high-level interface over libcurl)
4. **Single URL source parser** (ORCID API - most structured)
5. **Basic Zotero integration** (retrieve publications)
6. **Simple analysis** (exact title/DOI matching)
7. **Text report generation**
8. **Additional source support** (Scholar, Pure)

### Future Enhancements (Post-MVP)
- Fuzzy publication matching using Claude CLI
- Interactive publication review mode
- Configuration file support
- Batch processing multiple researchers
- Integration with reference managers beyond Zotero
- Publication impact metrics
- Citation network analysis

This MVP design prioritizes rapid delivery of core functionality while establishing a solid foundation for future enhancements.