# Documentation-Tests Sync Report

Generated: 2026-02-03

## Summary

| Metric | Value |
|--------|-------|
| Services Analyzed | 12 |
| Total Features | 145 |
| Total Flows | 42 |
| Total Tests | 318 |
| Average Coverage | 72.3% |

## Service Reports

---

## api-gateway

- **Features:** 14
- **Flows:** 5
- **Tests:** 92
- **Coverage:** 92.9%

**Status:** [OK] High coverage

**Generated Docs:**
- api-gateway/docs/features.md
- api-gateway/docs/flows.md

---

## agent-engine

- **Features:** 12
- **Flows:** 5
- **Tests:** 79
- **Coverage:** 66.7%

**Status:** [OK] Good coverage

**Missing Tests:**
- GET /health endpoint
- GET /status endpoint
- POST /tasks endpoint
- GET /tasks/{task_id} endpoint

**Generated Docs:**
- agent-engine/docs/features.md
- agent-engine/docs/flows.md

---

## dashboard-api

- **Features:** 12
- **Flows:** 4
- **Tests:** 38
- **Coverage:** 50.0%

**Status:** [OK] Acceptable coverage

**Missing Tests:**
- WebSocket subscription tests
- Real-time streaming tests

**Generated Docs:**
- dashboard-api/docs/features.md
- dashboard-api/docs/flows.md

---

## api-services/github-api

- **Features:** 12
- **Flows:** 4
- **Tests:** 10
- **Coverage:** 83.3%

**Status:** [OK] Good coverage

**Generated Docs:**
- api-services/github-api/docs/features.md
- api-services/github-api/docs/flows.md

---

## api-services/jira-api

- **Features:** 11
- **Flows:** 4
- **Tests:** 8
- **Coverage:** 90.9%

**Status:** [OK] High coverage

**Generated Docs:**
- api-services/jira-api/docs/features.md
- api-services/jira-api/docs/flows.md

---

## api-services/slack-api

- **Features:** 12
- **Flows:** 4
- **Tests:** 7
- **Coverage:** 87.5%

**Status:** [OK] Good coverage

**Generated Docs:**
- api-services/slack-api/docs/features.md
- api-services/slack-api/docs/flows.md

---

## api-services/sentry-api

- **Features:** 12
- **Flows:** 5
- **Tests:** 8
- **Coverage:** 91.7%

**Status:** [OK] High coverage

**Generated Docs:**
- api-services/sentry-api/docs/features.md
- api-services/sentry-api/docs/flows.md

---

## oauth-service

- **Features:** 15
- **Flows:** 5
- **Tests:** 6
- **Coverage:** 33.3%

**Status:** [LOW] Needs more tests

**Missing Tests:**
- Token storage tests
- Token refresh tests
- Token lookup tests
- Installation management tests
- Health check tests

**Generated Docs:**
- oauth-service/docs/features.md
- oauth-service/docs/flows.md

---

## task-logger

- **Features:** 14
- **Flows:** 4
- **Tests:** 38
- **Coverage:** 64.3%

**Status:** [OK] Good coverage

**Missing Tests:**
- Redis stream consumer tests
- API endpoint tests

**Generated Docs:**
- task-logger/docs/features.md
- task-logger/docs/flows.md

---

## gkg-service

- **Features:** 14
- **Flows:** 5
- **Tests:** 12
- **Coverage:** 85.7%

**Status:** [OK] Good coverage

**Generated Docs:**
- gkg-service/docs/features.md
- gkg-service/docs/flows.md

---

## llamaindex-service

- **Features:** 13
- **Flows:** 5
- **Tests:** 11
- **Coverage:** 69.2%

**Status:** [OK] Acceptable coverage

**Missing Tests:**
- Ticket search tests
- Docs search tests
- Collections endpoint tests

**Generated Docs:**
- llamaindex-service/docs/features.md
- llamaindex-service/docs/flows.md

---

## indexer-worker

- **Features:** 11
- **Flows:** 5
- **Tests:** 9
- **Coverage:** 59.1%

**Status:** [OK] Acceptable coverage

**Missing Tests:**
- GitHub source indexer tests
- Jira source indexer tests
- Confluence source indexer tests

**Generated Docs:**
- indexer-worker/docs/features.md
- indexer-worker/docs/flows.md

---

## Coverage Summary by Service

| Service | Features | Tested | Coverage |
|---------|----------|--------|----------|
| api-gateway | 14 | 13 | 92.9% |
| api-services/sentry-api | 12 | 11 | 91.7% |
| api-services/jira-api | 11 | 10 | 90.9% |
| api-services/slack-api | 12 | 10 | 87.5% |
| gkg-service | 14 | 12 | 85.7% |
| api-services/github-api | 12 | 10 | 83.3% |
| llamaindex-service | 13 | 9 | 69.2% |
| agent-engine | 12 | 8 | 66.7% |
| task-logger | 14 | 9 | 64.3% |
| indexer-worker | 11 | 6 | 59.1% |
| dashboard-api | 12 | 7 | 50.0% |
| oauth-service | 15 | 5 | 33.3% |

---

## Recommendations

### High Priority (Coverage < 50%)

1. **oauth-service**: Add comprehensive tests for token lifecycle

### Medium Priority (Coverage 50-70%)

1. **dashboard-api**: Add WebSocket tests
2. **indexer-worker**: Add source indexer tests
3. **task-logger**: Add Redis consumer tests

### Low Priority (Coverage > 70%)

1. Add health endpoint tests to all services
2. Add API endpoint integration tests

---

## How to Regenerate This Report

Use the `docs-tests-sync` skill:

1. Read service README.md and ARCHITECTURE.md
2. Extract features and flows
3. Analyze tests and match to features
4. Generate features.md and flows.md per service
5. Update this SYNC_REPORT.md
