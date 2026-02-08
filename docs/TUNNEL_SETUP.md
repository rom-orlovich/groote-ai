# Tunnel Setup Guide

To receive webhooks from GitHub, Jira, Slack, and other external services, you need a public URL. This guide covers two options: **zrok (recommended)** and **ngrok**.

## zrok (Recommended)

**zrok** is a free, open-source tunneling service with a permanent public URL. Unlike ngrok's free tier, zrok won't expire or require re-authentication.

### Benefits of zrok

- ✅ **Free forever** - No time limits or rate limits that reset
- ✅ **Permanent URL** - Your URL stays the same across restarts (`https://<your-share-name>.your-tunnel-domain.example`)
- ✅ **Stable** - No 2-hour session limits like ngrok free tier
- ✅ **Open source** - Transparent, community-driven

### One-Time Setup

Run this command to install zrok and reserve your permanent share name:

```bash
make tunnel-setup
```

This script will:

1. **Install zrok binary** to `~/.local/bin/zrok`
2. **Prompt you to create a free account** at https://myzrok.io
   - Check your email for the enable token
   - Run: `zrok enable <TOKEN_FROM_EMAIL>`
3. **Reserve a permanent share name** (e.g., `my-app`)
4. **Show your URL**: `https://<your-share-name>.your-tunnel-domain.example`

Then add to `.env`:

```bash
PUBLIC_URL=https://<your-share-name>.your-tunnel-domain.example
TUNNEL_SHARE_NAME=<your-share-name>
```

### Starting the Tunnel

Once setup is complete, start the tunnel anytime with:

```bash
make tunnel-zrok
```

The tunnel will:
- Display all webhook URLs
- Show OAuth callback URL
- Keep running in the foreground (Ctrl+C to stop)

**Example output:**

```
Starting zrok tunnel: https://<your-share-name>.your-tunnel-domain.example -> http://localhost:3005

Routes (via nginx on port 3005):
  /           -> external-dashboard (React SPA)
  /api/*      -> dashboard-api:5000
  /oauth/*    -> oauth-service:8010
  /webhooks/* -> api-gateway:8000
  /ws         -> dashboard-api:5000 (WebSocket)

Webhook URLs:
  GitHub: https://<your-share-name>.your-tunnel-domain.example/webhooks/github
  Jira:   https://<your-share-name>.your-tunnel-domain.example/webhooks/jira
  Slack:  https://<your-share-name>.your-tunnel-domain.example/webhooks/slack

OAuth callback: https://<your-share-name>.your-tunnel-domain.example/oauth/callback
```

### Using a Different Share Name

If your chosen name is taken, customize it:

```bash
TUNNEL_SHARE_NAME=my-unique-name make tunnel-setup
```

Then update `.env` with your chosen name.

---

## ngrok (Alternative)

**ngrok** is another popular tunneling service. Use this if you prefer or have an existing ngrok account.

### Setup

1. [Download ngrok](https://ngrok.com/download)
2. [Create a free account](https://dashboard.ngrok.com/signup) (optional for basic use)
3. Authenticate (if using account): `ngrok config add-authtoken <TOKEN>`

### Starting the Tunnel

```bash
make tunnel
```

Then copy the ngrok URL to `.env`:

```bash
PUBLIC_URL=https://your-domain.ngrok-free.app
```

### Important: ngrok Free Tier Limits

- ⚠️ **Session expires in 2 hours** - You must restart the tunnel regularly
- ⚠️ **URL changes each restart** - Must update `.env` and webhook configurations each time
- ⚠️ **Bandwidth limits** - May throttle high-volume webhooks

For production, consider ngrok's paid plans with persistent URLs.

---

## Configuration

### Using Public URLs in Services

All services automatically use `PUBLIC_URL`:

- **OAuth callbacks** point to `{PUBLIC_URL}/oauth/callback`
- **Webhook URLs** use `{PUBLIC_URL}/webhooks/{service}`
- **Dashboard frontend** is available at `{PUBLIC_URL}/`

### Updating Service Configurations

When you have a new public URL, update it in:

1. `.env` file → `PUBLIC_URL` environment variable
2. **GitHub** → Webhook settings with new URL
3. **Jira** → Webhook settings with new URL
4. **Slack** → Event subscription URLs with new URL

The system will automatically pick up the new `PUBLIC_URL` on next service restart.

---

## Troubleshooting

### "zrok not installed"

Install manually:

```bash
curl -sL https://github.com/openziti/zrok/releases/latest/download/zrok_$(uname -s | tr '[:upper:]' '[:lower:]')_amd64.tar.gz | tar -xz -C ~/.local/bin/
```

### "zrok not enabled"

Run account setup:

```bash
zrok enable <TOKEN_FROM_EMAIL>
make tunnel-setup
```

### "Share name already taken"

Choose a different name:

```bash
TUNNEL_SHARE_NAME=my-new-name make tunnel-setup
```

### Tunnel stops unexpectedly

The tunnel runs in foreground. Check for:
- Network interruptions
- Port 3005 conflicts (check `lsof -i :3005`)
- Service errors in logs (`make logs`)

Restart with `make tunnel-zrok`.

---

## Next Steps

1. Set up your tunnel: `make tunnel-setup`
2. Start the tunnel: `make tunnel-zrok`
3. Configure webhooks in GitHub, Jira, Slack with the URLs
4. Test by triggering a webhook (e.g., create a GitHub issue)
5. Check logs: `make logs` to see webhook processing
