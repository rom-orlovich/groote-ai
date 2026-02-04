# OAuth Service - Flows

## Process Flows

### GitHub OAuth Flow

```
[User] → Click "Install GitHub App"
              ↓
[OAuth Service] → Generate Authorization URL
              ↓
        [Include state, redirect_uri]
              ↓
[User] → Redirected to GitHub
              ↓
[GitHub] → User authorizes app
              ↓
[GitHub] → Redirect to /oauth/callback/github?code=xxx
              ↓
[OAuth Service] → Exchange code for token
              ↓
        [Store token with org_id]
              ↓
        [Return success page]
```

**Authorization URL:**
```
https://github.com/login/oauth/authorize
  ?client_id={client_id}
  &redirect_uri={callback_url}
  &state={state_token}
  &scope=repo,read:org
```

### Slack OAuth Flow

```
[User] → Click "Add to Slack"
              ↓
[OAuth Service] → Generate Authorization URL
              ↓
        [Include scopes, redirect_uri]
              ↓
[User] → Redirected to Slack
              ↓
[Slack] → User authorizes app
              ↓
[Slack] → Redirect to /oauth/callback/slack?code=xxx
              ↓
[OAuth Service] → Exchange code for token
              ↓
        [Store token with workspace_id]
              ↓
        [Return success page]
```

**Authorization URL:**
```
https://slack.com/oauth/v2/authorize
  ?client_id={client_id}
  &redirect_uri={callback_url}
  &scope=chat:write,channels:read
  &state={state_token}
```

### Jira OAuth Flow

```
[User] → Click "Connect Jira"
              ↓
[OAuth Service] → Generate Authorization URL
              ↓
        [Include scopes, redirect_uri]
              ↓
[User] → Redirected to Atlassian
              ↓
[Atlassian] → User authorizes app
              ↓
[Atlassian] → Redirect to /oauth/callback/jira?code=xxx
              ↓
[OAuth Service] → Exchange code for token
              ↓
        [Store token with site_id]
              ↓
        [Return success page]
```

**Authorization URL:**
```
https://auth.atlassian.com/authorize
  ?client_id={client_id}
  &redirect_uri={callback_url}
  &scope=read:jira-work,write:jira-work
  &state={state_token}
  &response_type=code
  &prompt=consent
```

### Token Lookup Flow

```
[API Service] → GET /oauth/token/github?org_id=xxx
                          ↓
                [Query PostgreSQL]
                          ↓
                [Installation Found?]
                     ↓         ↓
                  [Yes]       [No]
                     ↓         ↓
            [Check Expiry]  [Return 404]
                     ↓
            [Expired?]
               ↓      ↓
            [Yes]    [No]
               ↓      ↓
          [Refresh] [Return Token]
               ↓
          [Store New Token]
               ↓
          [Return Token]
```

**Token Response:**
```json
{
  "access_token": "gho_xxx...",
  "token_type": "bearer",
  "scopes": ["repo", "read:org"],
  "expires_at": "2026-02-04T12:00:00Z"
}
```

### Token Refresh Flow

```
[Token Lookup] → [Check Expiry]
                       ↓
              [expires_at < now?]
                       ↓
                    [Yes]
                       ↓
              [Load refresh_token]
                       ↓
              [Call Provider API]
                       ↓
              [Exchange for new tokens]
                       ↓
              [Update PostgreSQL]
                       ↓
              [Return new access_token]
```

**Refresh Request (GitHub):**
```
POST https://github.com/login/oauth/access_token
Content-Type: application/x-www-form-urlencoded

client_id={client_id}
&client_secret={client_secret}
&grant_type=refresh_token
&refresh_token={refresh_token}
```

### Installation Management Flow

```
[Dashboard] → GET /oauth/installations?platform=github
                          ↓
                [Query PostgreSQL]
                          ↓
                [Filter by platform]
                          ↓
                [Return installation list]

[Dashboard] → DELETE /oauth/installations/{id}
                          ↓
                [Load Installation]
                          ↓
                [Revoke Token at Provider]
                          ↓
                [Delete from PostgreSQL]
                          ↓
                [Return success]
```

**Installation Response:**
```json
{
  "installations": [
    {
      "id": "uuid",
      "platform": "github",
      "org_name": "acme-corp",
      "org_id": "12345",
      "scopes": ["repo", "read:org"],
      "status": "active",
      "created_at": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### Token Encryption Flow

```
[Store Token] → [Load ENCRYPTION_KEY]
                        ↓
               [Fernet Encrypt]
                        ↓
               [Store encrypted token]
                        ↓
               [PostgreSQL]

[Get Token] → [Load from PostgreSQL]
                      ↓
             [Fernet Decrypt]
                      ↓
             [Return plain token]
```

**Encryption:**
- Algorithm: Fernet (AES-128-CBC + HMAC-SHA256)
- Key: 32-byte URL-safe base64 encoded
- Encryption at rest for all tokens
