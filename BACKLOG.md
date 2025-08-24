# Development Backlog

## TODO (Ordered by Priority)
- [ ] #56: dead: remove duplicate author parsing functions
- [ ] #58: dead: remove duplicate progress tracking implementations
- [ ] #60: dead: remove redundant test fixtures
- [ ] #51: dead: remove unused imports across codebase
- [ ] #54: dead: remove obsolete configuration constants
- [ ] #57: dead: remove commented code blocks
- [ ] #59: dead: remove unused exception handlers
- [ ] #61: meta: dead code removal summary and verification

## DOING (Current Work)
- [x] #55: dead: remove redundant SourceError class hierarchy (branch: dead-55-redundant-source-error-hierarchy)

## DONE (Completed)
- [x] #52: dead: remove duplicate fuzzy matching implementations (PR #70)
- [x] #53: dead: remove unused private methods in sources module (completed in PR #69)
- [x] #50: dead: remove legacy ZoteroLibrary class and unused imports (PR #69)
- [x] #65: bug: URL validation is case-sensitive, should accept uppercase domains (PR #68)
- [x] #64: bug: fetch command doesn't validate output filename before API calls (resolved by PR #67)
- [x] #63: bug: file permission check happens after expensive API calls (branch: bug-63-file-permission-check-timing)
- [x] #62: bug: uncaught exception in Scholar source with empty search results (branch: bug-62-scholar-empty-results)