# Development Backlog

## TODO (Ordered by Priority)
- [ ] #64: bug: fetch command doesn't validate output filename before API calls
- [ ] #65: bug: URL validation is case-sensitive, should accept uppercase domains
- [ ] #50: dead: remove legacy `fetch_publications` method
- [ ] #53: dead: remove unused private methods in sources module
- [ ] #52: dead: remove duplicate fuzzy matching implementations
- [ ] #55: dead: remove redundant SourceError class hierarchy
- [ ] #56: dead: remove duplicate author parsing functions
- [ ] #58: dead: remove duplicate progress tracking implementations
- [ ] #60: dead: remove redundant test fixtures
- [ ] #51: dead: remove unused imports across codebase
- [ ] #54: dead: remove obsolete configuration constants
- [ ] #57: dead: remove commented code blocks
- [ ] #59: dead: remove unused exception handlers
- [ ] #61: meta: dead code removal summary and verification

## DOING (Current Work)

## DONE (Completed)
- [x] #63: bug: file permission check happens after expensive API calls (branch: bug-63-file-permission-check-timing)
- [x] #62: bug: uncaught exception in Scholar source with empty search results (branch: bug-62-scholar-empty-results)