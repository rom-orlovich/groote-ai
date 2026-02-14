# Tunnel Setup Guide

To receive webhooks from GitHub, Jira, Slack, and other external services, you need a public URL. You can use any tunnel provider or your production domain.

## Setting Your Public URL

Set `PUBLIC_URL` directly in `.env`:

```bash
PUBLIC_URL=https://your-domain.example.com
```

All services are proxied through nginx on port 3005:

```
PUBLIC_URL -> port 3005 -> nginx
  /           -> external-dashboard (React SPA)
  /api/*      -> dashboard-api:5000
  /oauth/*    -> oauth-service:8010
  /webhooks/* -> api-gateway:8000
  /ws         -> dashboard-api:5000 (WebSocket)
```

---

## Tunnel Providers

### zrok (Recommended)

Free, open-source tunneling with permanent URLs.

```bash
make tunnel-setup    # One-time: install zrok + reserve share name
make tunnel-zrok     # Start the tunnel
```

### ngrok (Alternative)

```bash
make tunnel          # Start ngrok tunnel
```

Then set `PUBLIC_URL` to your ngrok URL.

---

## Configuration

All services automatically use `PUBLIC_URL`:

- **OAuth callbacks** → `{PUBLIC_URL}/oauth/callback`
- **Webhook endpoints** → `{PUBLIC_URL}/webhooks/{service}`
- **Dashboard** → `{PUBLIC_URL}/`

### Updating Webhook URLs

When your public URL changes, update it in:

1. `.env` file
2. **GitHub** → Webhook settings
3. **Jira** → Webhook settings
4. **Slack** → Event subscription URLs

Services pick up the new `PUBLIC_URL` on restart.

---

## Troubleshooting

### "PUBLIC_URL is not set"

Set it in `.env` before starting a tunnel.

### Tunnel stops unexpectedly

Check for:
- Network interruptions
- Port 3005 conflicts (`lsof -i :3005`)
- Service errors (`make logs`)

---

## Next Steps

1. Set your `PUBLIC_URL` in `.env`
2. Start your tunnel: `make tunnel-zrok` or `make tunnel`
3. Configure webhooks in GitHub, Jira, Slack
4. Test by triggering a webhook (e.g., create a GitHub issue)
5. Check logs: `make logs`
