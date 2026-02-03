# api-services/github-api - Features

Auto-generated on 2026-02-03

## Overview

REST API wrapper for GitHub operations with multi-tenant OAuth support. Provides REST endpoints for GitHub operations supporting both single-tenant (PAT) and multi-tenant (OAuth) authentication.

## Features

### Issue Management [TESTED]

Create, read, update issues and comments

**Related Tests:**
- `test_get_issue`
- `test_create_issue`
- `test_add_comment_to_issue`

### PR Operations [TESTED]

Review PRs, post comments, manage reviews

**Related Tests:**
- `test_get_pull_request`
- `test_add_comment_to_pr`

### File Operations [TESTED]

Read and write repository files

**Related Tests:**
- `test_get_file_contents`
- `test_search_code`

### Repository Operations [TESTED]

List repos, get repository metadata

**Related Tests:**
- `test_get_repository`
- `test_list_branches`

### Branch Operations [TESTED]

Create and manage branches

**Related Tests:**
- `test_create_branch`
- `test_list_branches`

### Multi-Tenant Support [NEEDS TESTS]

Handle OAuth tokens per organization

### Response Posting [NEEDS TESTS]

Post agent responses back to GitHub

### GET /issues/{owner}/{repo}/{number} [TESTED]

Get issue details

**Related Tests:**
- `test_get_issue`

### POST /issues/{owner}/{repo}/{number}/comments [TESTED]

Post issue comment

**Related Tests:**
- `test_add_comment_to_issue`

### GET /pulls/{owner}/{repo}/{number} [TESTED]

Get PR details

**Related Tests:**
- `test_get_pull_request`

### GET /repos/{owner}/{repo}/contents/{path} [TESTED]

Read file contents

**Related Tests:**
- `test_get_file_contents`

### GET /repos/{owner}/{repo} [TESTED]

Get repository details

**Related Tests:**
- `test_get_repository`

## Test Coverage Summary

| Metric | Count |
|--------|-------|
| Total Features | 12 |
| Fully Tested | 10 |
| Partially Tested | 0 |
| Missing Tests | 2 |
| **Coverage** | **83.3%** |
