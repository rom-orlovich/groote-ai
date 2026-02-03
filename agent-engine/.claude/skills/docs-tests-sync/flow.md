# Docs-Tests Sync Flow

## Full Sync Workflow

### Step 1: Service Discovery

```
For each service directory:
1. Check for README.md
2. Check for docs/ARCHITECTURE.md
3. Check for .claude/CLAUDE.md
4. Check for tests/ directory
5. Add to service list with metadata
```

**Service metadata:**
- `name` - Service identifier
- `path` - Full path
- `doc_sources` - List of documentation files
- `test_path` - Path to tests directory

### Step 2: Documentation Extraction

#### Extract Features

Parse each documentation file:

```
1. Find "### Core Responsibilities" section
   - Extract numbered items: `\d+\.\s+\*\*([^*]+)\*\*[:\s]*([^\n]*)`

2. Find "## API Endpoints" table
   - Extract: `| endpoint | METHOD | description |`

3. Find agent/skill lists
   - Extract: `- \`name\` - description`

4. Find response codes
   - Extract: `- \`{code}\`: description`
```

#### Extract Flows

Parse for process flows:

```
1. Find "### {Service} Flow" sections
   - Services: GitHub, Jira, Slack, Sentry, Webhook, Task
   - Extract numbered steps

2. Find "## Architecture" section
   - Extract numbered processing steps

3. Find mermaid/sequence diagrams
   - Parse arrow connections: `A --> B: action`
```

### Step 3: Test Analysis

For each test file in `tests/`:

```
1. Parse Python AST
2. Find test functions (test_*)
3. Extract:
   - Function name
   - Docstring
   - Inferred features from name keywords
```

**Keyword extraction:**
- Split test name by underscore
- Match against feature keywords
- Score overlap

### Step 4: Coverage Matching

Match tests to features:

```
For each feature:
1. Extract keywords from feature name + description
2. For each test:
   - Extract keywords from test name + docstring
   - Calculate overlap score
3. If overlap >= 2 keywords OR (overlap == 1 AND feature has <= 2 keywords):
   - Add test to feature.related_tests
4. Assign coverage level:
   - TESTED: 2+ tests
   - PARTIAL: 1 test
   - NEEDS TESTS: 0 tests
```

### Step 5: Report Generation

Generate `features.md`:

```markdown
# {service} - Features

## Overview
{extracted from README first paragraph}

## Features

### {feature.name} [{coverage_badge}]
{feature.description}

**Related Tests:**
- `{test_name}`

## Test Coverage Summary
| Metric | Count |
|--------|-------|
| Total Features | X |
| Fully Tested | Y |
| Coverage | Z% |
```

Generate `flows.md`:

```markdown
# {service} - Flows

## Process Flows

### {flow.name} [{coverage_badge}]

**Steps:**
1. {step}
2. {step}

**Related Tests:**
- `{test_name}`
```

Generate `SYNC_REPORT.md`:

```markdown
# Documentation-Tests Sync Report

## Summary
| Services | Features | Flows | Tests | Coverage |
|----------|----------|-------|-------|----------|
| X        | Y        | Z     | W     | P%       |

## Service Reports
{per-service summary}
```

---

## Single Service Sync

When syncing a single service:

1. Read service documentation
2. Extract features and flows
3. Analyze tests in service `tests/`
4. Match coverage
5. Generate `docs/features.md` and `docs/flows.md`
6. Update master `SYNC_REPORT.md`

---

## Documentation Change Sync

When documentation changes:

1. Detect changed files (README.md, ARCHITECTURE.md)
2. Re-extract features/flows for affected service
3. Compare with existing `features.md`
4. Identify new/changed/removed features
5. For changed features:
   - Check if existing tests still match
   - Flag tests that may need updates
6. For new features:
   - Generate test suggestions
7. Update generated docs

---

## Test Change Sync

When tests change:

1. Detect changed test files
2. Re-analyze affected service tests
3. Re-match to features
4. Update coverage levels
5. Regenerate reports

---

## Test Suggestion Generation

For features with NEEDS TESTS:

```
1. Generate test name from feature:
   - Lowercase, replace spaces with underscores
   - Prefix with test_
   - Max 50 chars

2. Suggest test cases:
   - Happy path
   - Error handling
   - Edge cases

3. Output suggestion:
   "Missing test for '{feature}': Consider adding test_{name}"
```

---

## Running Tests After Sync

When `--run-tests` flag:

1. After generating docs for service
2. Run: `pytest {service}/tests/ -v --tb=short`
3. Capture result
4. If failures:
   - Add to report
   - Flag affected features
5. Timeout: 300 seconds per service
