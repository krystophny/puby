# Development Backlog

## CURRENT SPRINT (Defect Resolution & Architecture Alignment)

### CRITICAL Priority
- [ ] #91: perf: implement connection pooling for HTTP requests
- [ ] #92: test: achieve 80% test coverage for core modules

### HIGH Priority  
- [ ] #82: Tool continues processing when ORCID source fails with 404
- [ ] #90: refactor: split large modules to meet 500-line target
- [ ] #93: infra: add CI/CD pipeline and development tooling

### MEDIUM Priority
- [ ] #78: URL validation bypassed by Zotero validation
- [ ] #89: architecture: align DESIGN.md with current module structure
- [ ] #84: refactor: consolidate version number definition

### LOW Priority (Small Fixes)
- [ ] #79: refactor: remove unused contextlib import in pure_source.py
- [ ] #80: refactor: remove or implement placeholder _parse_api_response method
- [ ] #81: refactor: consolidate duplicate text normalization functions
- [ ] #83: refactor: remove unused _calculate_similarity static method in models.py

## DOING (Current Work)

## FUTURE SPRINTS

### Sprint 2: Performance Optimization
- Goal: Optimize import chain and reduce memory footprint
- Approach: Lazy loading, dependency analysis, profiling
- Key decisions: Identify and remove unnecessary dependencies

### Sprint 3: Documentation Update
- Goal: Complete documentation alignment and user guides
- Approach: Sync DESIGN.md with implementation, add examples
- Key decisions: Single source of truth for architecture docs

## DONE (Completed)