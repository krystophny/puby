# Development Backlog

## TODO (Ordered by Priority)
- [ ] #51: dead: remove unused imports across codebase
- [ ] #54: dead: remove obsolete configuration constants
- [ ] #57: dead: remove commented code blocks
- [ ] #59: dead: remove unused exception handlers
- [ ] #61: meta: dead code removal summary and verification

## DOING (Current Work)
- [x] #60: code duplication: User-Agent header construction repeated in multiple sources (branch: dead-60-user-agent-duplication)

## DONE (Completed)
- [x] #58: dead: eliminate duplicate author parsing logic across sources (PR #73)
- [x] #56: dead: eliminate duplicate similarity calculation methods (PR #72)
- [x] #55: dead: eliminate duplicate Zotero API key URLs and error messages (PR #71)
- [x] #52: dead: remove duplicate fuzzy matching implementations (PR #70)
- [x] #53: dead: remove unused private methods in sources module (completed in PR #69)
- [x] #50: dead: remove legacy ZoteroLibrary class and unused imports (PR #69)
- [x] #65: bug: URL validation is case-sensitive, should accept uppercase domains (PR #68)
- [x] #64: bug: fetch command doesn't validate output filename before API calls (resolved by PR #67)
- [x] #63: bug: file permission check happens after expensive API calls (branch: bug-63-file-permission-check-timing)
- [x] #62: bug: uncaught exception in Scholar source with empty search results (branch: bug-62-scholar-empty-results)