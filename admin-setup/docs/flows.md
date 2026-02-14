# Admin Setup - Flows

## Process Flows

### Authentication Flow

```
[Admin] -> Enter token -> [AuthGate Component]
                                  |
                          [POST /api/auth {token}]
                                  |
                      [Compare with ADMIN_SETUP_TOKEN]
                              |           |
                         [Invalid]    [Valid]
                            |            |
                      [401 Error]  [Set httpOnly cookie]
                                         |
                                  [Show setup wizard]
```

**Processing Steps:**
1. Admin enters token in AuthGate input
2. POST request sent to /api/auth with token
3. Server compares against ADMIN_SETUP_TOKEN env var
4. On match, sets admin_session cookie (httpOnly, strict SameSite, 24h TTL)
5. Returns {authenticated: true}
6. AuthGate reveals the setup wizard

### Infrastructure Check Flow

```
[Setup Wizard] -> GET /api/setup/infrastructure -> [Validators]
                                                       |
                                              [Check PostgreSQL]
                                                  |          |
                                             [Healthy]   [Failed]
                                                  |          |
                                              [Check Redis]  |
                                                  |          |
                                             [Return Results]
```

**Processing Steps:**
1. Wizard requests infrastructure health check
2. Validator opens async connection to PostgreSQL
3. Execute `SELECT 1` to verify connectivity
4. Validator opens async connection to Redis
5. Execute `PING` to verify connectivity
6. Return health status for both services

### Step Configuration Save Flow

```
[Admin] -> Fill form -> [ServiceStep Component]
                               |
                        [POST /api/setup/steps/{step_id}]
                               |
                        [Validate cookie session]
                               |
                     [For each config key/value:]
                               |
                        [Is key sensitive?]
                           |          |
                        [Yes]       [No]
                          |           |
                   [Encrypt value]  [Store plaintext]
                          |           |
                   [Upsert to setup_config table]
                               |
                        [Update setup_state]
                               |
                        [Advance to next step]
                               |
                        [Return {success, current_step, progress}]
```

**Processing Steps:**
1. Admin fills OAuth credentials in step form
2. POST request with configs dict and skip flag
3. Server validates session cookie
4. For each key-value pair in CATEGORY_MAP
5. Encrypt sensitive values (CLIENT_SECRET, SIGNING_SECRET, etc.)
6. Upsert into setup_config with scope="admin"
7. Update setup_state: mark step complete, advance current_step
8. Calculate progress_percent from completed + skipped / total
9. Return updated progress to frontend

### Credential Validation Flow

```
[Admin] -> Click "Validate" -> [POST /api/setup/validate/{service}]
                                        |
                              [Route to service validator]
                                    |        |        |
                              [GitHub]  [Jira]   [Slack]
                                 |         |         |
                          [Create JWT] [HTTP GET] [Check ID]
                                 |         |         |
                          [GET /app]  [/rest/api] [Return OK]
                                 |         |
                           [200 = valid] [Reachable = valid]
                                 |         |
                          [Return {valid, message}]
```

**Processing Steps:**
1. Admin clicks validate button for a service
2. POST request with current config values
3. Router dispatches to appropriate validator
4. GitHub: Create JWT from App ID + private key, call GitHub API
5. Jira: HTTP GET to site URL's REST endpoint
6. Slack: Check client ID presence (OAuth validates later)
7. Return validation result with human-readable message

### Configuration Export Flow

```
[Admin] -> Click "Export" -> [GET /api/setup/export]
                                     |
                             [Fetch all configs from DB]
                                     |
                             [Decrypt sensitive values]
                                     |
                             [Sort by category]
                                     |
                             [Generate .env format]
                                     |
                             [Append derived paths]
                                     |
                             [Return {content, filename}]
```

**Processing Steps:**
1. Admin requests export on review step
2. Service fetches all configs with scope="admin"
3. Decrypt sensitive values using Fernet
4. Sort configs by category for grouping
5. Generate KEY=VALUE lines grouped by category
6. Append GITHUB_PRIVATE_KEY_PATH if private key file configured
7. Return .env content and suggested filename

### Setup Completion Flow

```
[Admin] -> Click "Complete" -> [POST /api/setup/complete]
                                       |
                               [Update setup_state]
                                       |
                               [Set is_complete = true]
                                       |
                               [Set progress = 100%]
                                       |
                               [Set completed_at timestamp]
                                       |
                               [Return {status: "complete"}]
```

**Processing Steps:**
1. Admin clicks complete on review step
2. Server loads setup_state from database
3. Set is_complete to true
4. Set progress_percent to 100
5. Record completed_at timestamp
6. Return success confirmation

### Setup Reset Flow

```
[Admin] -> Click "Reset" -> [POST /api/setup/reset]
                                    |
                            [Reset setup_state]
                                    |
                            [Delete all setup_config rows]
                                    |
                            [Return to welcome step]
```

**Processing Steps:**
1. Admin requests setup reset
2. Reset setup_state: is_complete=false, current_step="welcome", progress=0
3. Clear completed_steps and skipped_steps
4. Delete all rows from setup_config where scope="admin"
5. Return {status: "reset"}
