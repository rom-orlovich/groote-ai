# Docs-Tests Sync Templates

## Features Document Template

```markdown
# {service_name} - Features

Auto-generated on {date}

## Overview

{overview_from_readme}

## Features

### {feature_name} [{coverage_badge}]

{feature_description}

**Related Tests:**
- `{test_name}`
- `{test_name}`

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | {total} |
| Fully Tested | {full} |
| Partially Tested | {partial} |
| Missing Tests | {missing} |
| **Coverage** | **{percentage}%** |
```

---

## Flows Document Template

```markdown
# {service_name} - Flows

Auto-generated on {date}

## Process Flows

### {flow_name} [{coverage_badge}]

**Steps:**
1. {step_1}
2. {step_2}
3. {step_3}

**Related Tests:**
- `{test_name}`

## Flow Coverage Summary

| Metric | Count |
|--------|-------|
| Total Flows | {total} |
| Fully Tested | {full} |
| Partially Tested | {partial} |
| Missing Tests | {missing} |
| **Coverage** | **{percentage}%** |
```

---

## Sync Report Template

```markdown
# Documentation-Tests Sync Report

Generated: {datetime}

## Summary

| Metric | Value |
|--------|-------|
| Services | {service_count} |
| Total Features | {feature_count} |
| Total Flows | {flow_count} |
| Total Tests | {test_count} |
| Average Coverage | {avg_coverage}% |

## Service Reports

## {service_name}

- **Features:** {count}
- **Flows:** {count}
- **Tests:** {count}
- **Coverage:** {percentage}%

**Missing Tests:**
- Feature: {feature_name}
- Flow: {flow_name}

**Generated Docs:**
- {service}/docs/features.md
- {service}/docs/flows.md

---
```

---

## Coverage Badge Formats

| Coverage | Badge |
|----------|-------|
| Full (2+ tests) | `[TESTED]` |
| Partial (1 test) | `[PARTIAL]` |
| None (0 tests) | `[NEEDS TESTS]` |

---

## Test Suggestion Template

```
Missing test for feature '{feature_name}':
Consider adding test_{suggested_name}

Suggested test cases:
- Happy path: test_{name}_success
- Error case: test_{name}_invalid_input
- Edge case: test_{name}_empty_input
```

---

## Service Report Entry Template

```markdown
## {service_name}

- **Features:** {feature_count}
- **Flows:** {flow_count}
- **Tests:** {test_count}
- **Coverage:** {coverage}%

**Missing Tests:**
- Feature: {missing_feature_1}
- Feature: {missing_feature_2}
- Flow: {missing_flow_1}
{if more than 5: "- ... and {remaining} more"}

**Generated Docs:**
- {service}/docs/features.md
- {service}/docs/flows.md
```

---

## Console Output Template

```
Discovered {count} services

Processing: {service_name}
  - Extracted {feature_count} features, {flow_count} flows
  - Found {test_count} tests
  - Generated: features.md
  - Generated: flows.md
  - Test suggestions: {suggestion_count}

============================================================
SYNC COMPLETE
============================================================
  [{status}] {service_name}: {coverage}% coverage
  [{status}] {service_name}: {coverage}% coverage

Status: OK (>=50%) or LOW (<50%)
```

---

## Gap Analysis Template

```markdown
### Coverage Gaps for {service_name}

**Untested Features:**
1. {feature_name} - {description}
   Suggested test: test_{suggested_name}

**Untested Flows:**
1. {flow_name}
   Steps not covered: {uncovered_steps}
   Suggested test: test_{suggested_name}_flow

**Recommendations:**
- Add unit tests for {feature}
- Add integration test for {flow}
- Consider E2E test for complete workflow
```
