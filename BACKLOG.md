# Development Backlog

## TODO (Ordered by Priority)

## DOING (Current Work)

## DONE (Completed)
- [x] #61: meta: dead code removal summary and verification (completed)
- [x] #59: fix fetch command misleading documentation (PR #77)
- [x] #57: dead: remove unused ORCIDConfig class (PR #76)
- [x] #54: dead: remove unused load_api_keys export in __init__.py (PR #75)
- [x] #51: dead: remove unused _initialize_zotero function in cli.py (already resolved in previous cleanup)
- [x] #60: code duplication: User-Agent header construction repeated in multiple sources (PR #74)
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