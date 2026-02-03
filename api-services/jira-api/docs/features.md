# api-services/jira-api - Features

Auto-generated on 2026-02-03

## Overview

REST API wrapper for Jira operations with issue and project management. Provides endpoints for issue management, comment posting, JQL search, and project operations.

## Features

### Issue Management [TESTED]

Create, read, update Jira issues

**Related Tests:**
- `test_get_issue`
- `test_create_issue`
- `test_update_issue`

### Comment Posting [TESTED]

Post agent responses to Jira tickets

**Related Tests:**
- `test_add_comment_to_issue`

### JQL Search [TESTED]

Execute JQL queries to find issues

**Related Tests:**
- `test_search_issues_with_jql`

### Transition Management [TESTED]

Move issues through workflow states

**Related Tests:**
- `test_transition_issue`
- `test_get_transitions`

### Project Operations [TESTED]

List projects and project metadata

**Related Tests:**
- `test_list_projects`
- `test_get_project`

### Response Posting [TESTED]

Post agent responses back to Jira tickets

**Related Tests:**
- `test_add_comment_to_issue`

### GET /issues/{issue_key} [TESTED]

Get issue details

**Related Tests:**
- `test_get_issue`

### POST /issues/{issue_key}/comments [TESTED]

Post issue comment

**Related Tests:**
- `test_add_comment_to_issue`

### POST /issues/{issue_key}/transitions [TESTED]

Transition issue

**Related Tests:**
- `test_transition_issue`

### GET /search [TESTED]

Execute JQL query

**Related Tests:**
- `test_search_issues_with_jql`

### GET /health [NEEDS TESTS]

Health check endpoint

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 11 |
| Fully Tested | 10 |
| Partially Tested | 0 |
| Missing Tests | 1 |
| **Coverage** | **90.9%** |
