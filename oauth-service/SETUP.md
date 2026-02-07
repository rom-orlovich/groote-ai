# OAuth Service Setup Guide

## Quick Start

```bash
# 1. Copy environment file
cd groote-ai/oauth-service && cp .env.example .env

# 2. Configure OAuth credentials in .env (see below)

# 3. Start service
cd ../.. && docker-compose up -d oauth-service postgres

# 4. Verify
curl http://localhost:8010/health
```

## OAuth App Configuration

### GitHub (OAuth App)

1. GitHub Settings → Developer settings → OAuth Apps → New OAuth App
2. Set callback URL: `http://localhost:8010/oauth/callback/github`
3. Copy Client ID and Secret → add to `.env`:
   ```bash
   GITHUB_CLIENT_ID=xxx
   GITHUB_CLIENT_SECRET=xxx
   ```

### GitHub App (Recommended)

1. GitHub Settings → Developer settings → GitHub Apps → New GitHub App
2. Set callback URL: `{PUBLIC_URL}/oauth/callback/github`
3. Set permissions: Repository (R&W), Issues (R&W), Pull Requests (R&W)
4. On the app page, scroll to **Private keys** → click **Generate a private key**
5. A `.pem` file will download to your computer
6. Place the `.pem` file in the `secrets/` directory:
   ```bash
   mkdir -p secrets
   cp ~/Downloads/<app-name>.<date>.private-key.pem secrets/github-private-key.pem
   ```
7. Add to the root `.env`:
   ```bash
   GITHUB_APP_ID=123456
   GITHUB_APP_NAME=your-app
   GITHUB_CLIENT_ID=Iv1.xxx
   GITHUB_CLIENT_SECRET=xxx
   GITHUB_WEBHOOK_SECRET=xxx
   GITHUB_PRIVATE_KEY_PATH=/secrets/github-private-key.pem
   GITHUB_PRIVATE_KEY_FILE=./secrets/github-private-key.pem
   ```

> **Why two variables?**
> - `GITHUB_PRIVATE_KEY_FILE` — host path used by Docker Compose to mount the file into the container
> - `GITHUB_PRIVATE_KEY_PATH` — container path where the app reads the key
>
> PEM private keys are multiline and cannot be stored directly in `.env` files.
> The `secrets/` directory is already in `.gitignore`.

### Slack

1. [api.slack.com/apps](https://api.slack.com/apps) → Create New App
2. OAuth & Permissions → Add redirect URL: `http://localhost:8010/oauth/callback/slack`
3. Basic Information → Copy Client ID, Secret, Signing Secret
4. Generate state secret: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
5. Add to `.env`:
   ```bash
   SLACK_CLIENT_ID=xxx
   SLACK_CLIENT_SECRET=xxx
   SLACK_SIGNING_SECRET=xxx
   SLACK_STATE_SECRET=xxx
   ```

### Jira

1. [developer.atlassian.com](https://developer.atlassian.com/console/myapps/) → Create → OAuth 2.0 (3LO)
2. Set callback URL: `http://localhost:8010/oauth/callback/jira`
3. Copy Client ID and Secret → add to `.env`:
   ```bash
   JIRA_CLIENT_ID=xxx
   JIRA_CLIENT_SECRET=xxx
   ```

## Environment Variables

Generate encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add to `.env`:

```bash
PORT=8010
BASE_URL=http://localhost:8010  # Use https:// for production
DATABASE_URL=postgresql+asyncpg://agent:agent@postgres:5432/agent_system
TOKEN_ENCRYPTION_KEY=your_generated_key
# ... OAuth credentials from above
```

**Important**: OAuth callback URLs must match `{BASE_URL}/oauth/callback/{platform}`

## Testing

```bash
# Start OAuth flow
open http://localhost:8010/oauth/install/github

# List installations
curl http://localhost:8010/oauth/installations

# Get token
curl http://localhost:8010/oauth/token/github?org_id=your_org_id
```

## Troubleshooting

**Database issues**: `docker-compose logs postgres`

**GitHub "callback_failed"**: Check logs for the actual error:
```bash
docker logs groote-ai-oauth-service-1 2>&1 | grep "oauth_callback_error"
```
- `"Could not parse the provided public key"` → the `.pem` file is not mounted. Verify `GITHUB_PRIVATE_KEY_FILE` points to your `.pem` file and run `docker exec groote-ai-oauth-service-1 ls -la /secrets/github-private-key.pem`
- `"decryption_failed"` in dashboard-api logs → `TOKEN_ENCRYPTION_KEY` changed. Re-enter credentials in the Setup Wizard at `/setup`

**Callback errors**: Verify URLs match exactly in OAuth app settings and `BASE_URL`

**Service not starting**: `docker-compose logs oauth-service`

**Port conflicts**: Update port in `docker-compose.yml`, `.env`, and OAuth app callback URLs

## Production Deployment

### Infrastructure

**Kubernetes:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth-service
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: oauth-service
          image: your-registry/oauth-service:latest
          ports:
            - containerPort: 8010
          envFrom:
            - secretRef:
                name: oauth-secrets
          env:
            - name: BASE_URL
              value: "https://oauth.yourdomain.com"
          livenessProbe:
            httpGet:
              path: /health
              port: 8010
```

**Docker Compose:**

```yaml
services:
  oauth-service:
    build: ./oauth-service
    restart: always
    environment:
      - BASE_URL=https://oauth.yourdomain.com
    env_file:
      - .env.production
    deploy:
      replicas: 2
```

### Configuration

**Secrets Management:**

```bash
# AWS Secrets Manager
aws secretsmanager create-secret --name oauth-service/production --secret-string file://secrets.json

# Kubernetes
kubectl create secret generic oauth-secrets --from-literal=GITHUB_CLIENT_ID=xxx
```

**OAuth App Callbacks (Production):**

- GitHub: `https://oauth.yourdomain.com/oauth/callback/github`
- Slack: `https://oauth.yourdomain.com/oauth/callback/slack`
- Jira: `https://oauth.yourdomain.com/oauth/callback/jira`

**Environment Variables:**

```bash
BASE_URL=https://oauth.yourdomain.com
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/agent_system
# ... OAuth credentials from secrets manager
```

### Security & Monitoring

- [ ] HTTPS (TLS 1.2+)
- [ ] Secrets in secrets manager (not code)
- [ ] Rate limiting (100 req/min per IP)
- [ ] Health checks: `curl https://oauth.yourdomain.com/health`
- [ ] Monitoring alerts for service down/errors

### Deployment

```bash
docker build -t your-registry/oauth-service:v1.0.0 ./oauth-service
docker push your-registry/oauth-service:v1.0.0
kubectl set image deployment/oauth-service oauth-service=your-registry/oauth-service:v1.0.0
```

See [README.md](./README.md) for API documentation.
