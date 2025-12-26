# Portal Backend Architecture Analysis

**Date**: 2025-01-08  
**Purpose**: Analysis of Portal Backend for MVP and multi-tenant future

## Current State

### Database Structure

**account_users table** (2 users currently):
- ✅ `id` (UUID, primary key, matches auth.users.id)
- ✅ `email` (required, unique)
- ✅ `agent_zero_api_key` (nullable)
- ✅ `agent_zero_url` (nullable, default: http://localhost:8080)
- ✅ `agent_zero_username` (nullable)
- ✅ `agent_zero_password_encrypted` (nullable)
- ✅ `agent_zero_api_key_retrieved_at` (nullable)
- ✅ `agent_zero_instance_id` (nullable)

**Current Users**:
1. `info@silveraiautomation.com` - Has credentials, **NO API key** ❌
2. `test@portal.sys` - No credentials, no API key

### User Creation Flow

**Current Behavior**:
- ❌ **No automatic trigger** from `auth.users` → `account_users`
- ✅ Users are created when:
  - They call `/api/user/initialize-profile` (explicit initialization)
  - They call `/api/user/connect-agent-zero` (implicit creation via `store_agent_zero_credentials`)

**This is fine for MVP** - users get created on first use.

### Connection Issue

**Status**: ✅ **FIXED** - Connection bug resolved (January 2025)

**Problem (Resolved)**: Users had credentials stored but `agent_zero_api_key` was NULL (0/2 users had API keys)

**Root Cause**: The `extract_api_key()` function in `app/services/agent_zero_client.py` was looking for a settings section with `id == 'mcp'`, but the actual section ID in Agent Zero's settings structure is `'mcp_server'`.

**Fix Applied**: Updated line 352 in `app/services/agent_zero_client.py` to look for section `id == 'mcp_server'` instead of `'mcp'`.

**Current Status**: API keys are now properly extracted and stored when users connect to Agent Zero.

## Architecture Decision: Keep `app/FRONTEND_CONTRACT.md`

### Why Keep It

✅ **For MVP**:
- Handles Supabase authentication (your login portal)
- Manages credential storage (encrypted passwords)
- API key caching (avoids repeated auth)
- Settings proxy (REST API for Agent Zero settings)

✅ **For Future Multi-Tenant**:
- Foundation for per-client instance management
- Already stores `agent_zero_url` per user (can be enhanced)
- Centralized auth and credential management
- Ready for instance provisioning endpoints

### What Makes It "Messy"

1. **Two separate frontend contracts**:
   - `agui-integration-kit/FRONTEND_CONTRACT.md` - AG-UI protocol (real-time)
   - `app/FRONTEND_CONTRACT.md` - Portal Backend API (REST, auth, provisioning)

2. **Different purposes**:
   - AG-UI: Direct connection to Agent Zero for chat/streaming
   - Portal Backend: Authentication, provisioning, settings management

### Recommended Organization

**Option 1: Keep Separate (Recommended for MVP)**
```
agui-integration-kit/
  └── FRONTEND_CONTRACT.md (AG-UI protocol)

app/
  └── FRONTEND_CONTRACT.md (Portal Backend API)
  └── README.md (Links to both contracts)
```

**Option 2: Rename for Clarity**
```
agui-integration-kit/
  └── FRONTEND_CONTRACT.md → AGUI_PROTOCOL.md

app/
  └── FRONTEND_CONTRACT.md → PORTAL_API.md
```

**Option 3: Consolidate (Not recommended - they serve different purposes)**

## Recommendations

### For MVP (Now)

1. ✅ **Keep `app/FRONTEND_CONTRACT.md`** - It's needed for Portal Backend API
2. ✅ **Keep current user creation flow** - No automatic trigger needed
3. ✅ **Fix connection issue** - Debug why API keys aren't being stored
4. ✅ **Use single Agent Zero instance** - Per-client instances can wait

### For Future Multi-Tenant

1. **Add instance provisioning endpoint**:
   ```python
   POST /api/user/provision-instance
   # Creates new Agent Zero instance (Docker container/VM)
   # Stores instance URL in account_users.agent_zero_url
   ```

2. **Use stored `agent_zero_url` per user** (instead of env var):
   ```python
   # In routes/agent_zero.py
   user_record = db.get_user_by_id(user['id'])
   agent_zero_url = (
       user_record.get('agent_zero_url') or 
       Config.AGENT_ZERO_URL  # Fallback for shared instance
   )
   ```

3. **Template-based instance creation**:
   - Store latest Argent template
   - Copy on provisioning
   - Version management

### Hybrid Architecture (Future)

```
Frontend Flow:
1. Login → Supabase Auth → Get JWT
2. Check instance → Portal Backend (/api/user/agent-zero-status)
3. Provision if needed → Portal Backend (/api/user/provision-instance)
4. Get instance URL → Portal Backend (/api/user/agent-zero-status)
5. Connect directly → AG-UI Client (bypass Portal Backend)
```

**Portal Backend handles**:
- ✅ Authentication (Supabase JWT)
- ✅ Instance provisioning & lifecycle
- ✅ Settings management (REST API)
- ✅ Instance discovery

**AG-UI handles**:
- ✅ Real-time chat/streaming (direct to Agent Zero)
- ✅ Better performance (no proxy overhead)

## Next Steps

1. ✅ **Connection issue resolved** - Bug fixed, API keys are now properly stored

2. ✅ **Documentation updated** - Complete integration flow documented in `app/FRONTEND_CONTRACT.md`

3. **For future**: Plan instance provisioning when needed for multi-tenant support

## Questions to Answer

1. ✅ **Why are API keys not being stored?** - **RESOLVED**: Bug in API key extraction (wrong section ID) has been fixed

2. ✅ **Do you need to delete users?** - **No, users don't need to be deleted** - Existing users can retry connection and API keys will now be stored correctly

3. ✅ **Should we add auto-creation trigger?** - **Not needed for MVP** - Current flow (create on first use) is fine, can add trigger later if needed

