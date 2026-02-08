# Migration Guide: Admin Setup Service & User Settings

This document describes the architectural changes in the recent refactoring.

## Overview

The system has been restructured to separate **admin system configuration** from **user-level settings**:

- **Admin Setup Service** (port 8015): System OAuth app credentials configuration (admin-only)
- **User Settings in Dashboard**: User-scoped AI provider and agent scaling configuration

## What Changed

### 1. Setup Wizard Removed

**Before**:
- `/setup` route exposed system configuration publicly
- All users saw OAuth app setup steps
- Setup wizard included sensitive credentials

**After**:
- `/setup` route removed
- Setup is admin-only at http://localhost:8015
- Requires token authentication

### 2. Admin Setup Service (New)

**Location**: Port 8015 + React frontend

**Features**:
- Token-based authentication (`ADMIN_SETUP_TOKEN` from .env)
- System OAuth app configuration (GitHub, Jira, Slack)
- Credential validation before saving
- Configuration export (.env format)

**Usage**:
```bash
# Access admin setup
curl -H "X-Admin-Token: your-token" http://localhost:8015/api/setup/status

# Or open browser
http://localhost:8015/?token=your-token
```

### 3. User Settings in Dashboard

**New Routes**:
- `/install` - OAuth connection page (user-facing)
- `/settings/ai-provider` - User AI configuration
- `/settings/agents` - Agent scaling configuration

**Features**:
- Users configure their own AI provider (Claude/Cursor) + API keys
- Users scale agents (1-20) for task execution
- Users connect/disconnect from configured platforms
- Settings stored per-user in `user_settings` table

### 4. Database Changes

#### New Table: `user_settings`
```sql
CREATE TABLE user_settings (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    is_sensitive BOOLEAN DEFAULT false,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, category, key)
);
```

#### Updated Table: `setup_config`
```sql
ALTER TABLE setup_config ADD COLUMN scope VARCHAR(20) DEFAULT 'admin';
```

- `scope=admin`: OAuth app credentials (admin-only)
- `scope=system`: Infrastructure config (public URL, encryption keys)

## Migration Steps

### For Existing Deployments

1. **Backup database** (optional but recommended)

2. **Run migrations**:
   ```bash
   # Add scope column to setup_config
   ALTER TABLE setup_config ADD COLUMN scope VARCHAR(20) DEFAULT 'admin';

   # Create user_settings table
   CREATE TABLE user_settings (
       id UUID PRIMARY KEY,
       user_id VARCHAR(255) NOT NULL,
       category VARCHAR(50) NOT NULL,
       key VARCHAR(100) NOT NULL,
       value TEXT NOT NULL,
       is_sensitive BOOLEAN DEFAULT false,
       updated_at TIMESTAMP DEFAULT NOW(),
       UNIQUE(user_id, category, key)
   );
   ```

3. **Update .env**:
   ```bash
   # Add admin setup token (generate a strong random token)
   ADMIN_SETUP_TOKEN=your-secure-admin-token-here
   ```

4. **Rebuild and restart**:
   ```bash
   docker-compose up --build
   ```

### For New Deployments

1. **Run `make init`** to generate .env with `ADMIN_SETUP_TOKEN`

2. **Run `make up`** to start all services

3. **Access admin setup**:
   - http://localhost:8015
   - Enter token from `ADMIN_SETUP_TOKEN` env var

## API Changes

### New Endpoints

#### Admin Setup Service
```
POST /api/setup/status         # Get setup status (requires token)
POST /api/setup/complete       # Mark setup complete (requires token)
```

#### Dashboard API - User Settings
```
POST /api/user-settings/ai-provider           # Save AI config
GET /api/user-settings/ai-provider            # Get AI config
POST /api/user-settings/ai-provider/test      # Test connection
POST /api/user-settings/agent-scaling         # Save agent count
GET /api/user-settings/agent-scaling          # Get agent count
DELETE /api/user-settings/{category}/{key}    # Delete setting
```

### Removed Endpoints

```
GET /setup                      # Setup wizard (removed)
```

## User Flows

### Admin: Configure OAuth Apps

1. Access http://localhost:8015
2. Enter ADMIN_SETUP_TOKEN
3. Follow OAuth app setup wizard
4. Save credentials to database

### User: Configure AI Provider

1. Access http://localhost:3005/settings/ai-provider
2. Select provider (Claude/Cursor)
3. Enter API key
4. Test connection
5. Save settings

### User: Scale Agents

1. Access http://localhost:3005/settings/agents
2. Adjust agent count (1-20)
3. See estimated monthly cost
4. Apply scaling

### User: Connect OAuth Platforms

1. Access http://localhost:3005/install
2. See platforms configured by admin
3. Click "Connect" for each platform
4. Complete OAuth flow
5. Status shows "Connected"

## Backward Compatibility

- Old `/setup` bookmarks will 404 (no redirect)
- All existing data is preserved
- No breaking changes to task processing

## Troubleshooting

**"Invalid admin token" error**:
- Verify `ADMIN_SETUP_TOKEN` is set in .env
- Verify you're sending the correct token

**"AI Provider Settings not saving"**:
- Verify user is authenticated (Bearer token)
- Check Dashboard API logs for errors
- Ensure database has `user_settings` table

**"Platform not showing in /install"**:
- Admin must configure OAuth app first at http://localhost:8015
- Check `setup_config` table for `scope=admin` entries

## Support

For questions or issues:
1. Check service health: `make health`
2. Check logs: `docker-compose logs service-name`
3. Review `.claude/rules/microservices.md` for architecture details
