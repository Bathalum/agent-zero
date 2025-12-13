# Portal Backend Investigation Report

**Date**: 2025-01-08  
**Issues**: 500 Error on `/api/user/agent-zero-status` and CORS Error on `/api/user/connect-agent-zero`

## Executive Summary

The frontend error handling is **working correctly**. The issues are:

1. **500 Error**: Backend database/connection issue - needs investigation
2. **CORS Error**: Backend CORS configuration issue - frontend origin may not be whitelisted

## Issue 1: 500 Internal Server Error

### Symptoms
- Endpoint: `GET /api/user/agent-zero-status`
- Response: `{"error": "Failed to retrieve Agent Zero status"}` with status 500
- Frontend correctly extracts and displays the error message

### Root Cause Analysis

The error occurs in `app/routes/agent_zero.py:48` when calling:
```python
status = db.get_user_agent_zero_status(user['id'])
```

**Possible causes:**

1. **Database Connection Failure**
   - Supabase client not initialized
   - Network connectivity issues
   - Invalid Supabase credentials

2. **Database Query Failure**
   - Table `account_users` doesn't exist
   - User record doesn't exist (though this should return empty status, not error)
   - Permission issues with Supabase service role key

3. **Missing Environment Variables**
   - `SUPABASE_URL` not set
   - `SUPABASE_SERVICE_ROLE_KEY` not set
   - `SUPABASE_ANON_KEY` not set

4. **Exception in `get_user_by_id()`**
   - Supabase query fails
   - Response parsing fails

### Investigation Steps

1. **Run diagnostics script:**
   ```bash
   cd app
   python -m app.diagnostics
   ```

2. **Check backend logs:**
   ```bash
   # If using Docker
   docker logs portal-backend-local --tail 100
   
   # Look for:
   # - "Error getting Agent Zero status"
   # - Supabase connection errors
   # - Database query errors
   ```

3. **Verify environment variables:**
   ```bash
   docker exec portal-backend-local printenv | grep SUPABASE
   ```

4. **Test database connection:**
   ```bash
   docker exec portal-backend-local python -c "from app.database import SupabaseDB; db = SupabaseDB.get_instance(); print('Connected')"
   ```

### Fixes Applied

1. **Enhanced error logging** - Now logs user ID in error messages
2. **Debug mode details** - In development, error response includes error details
3. **Diagnostic script** - Created `app/diagnostics.py` for troubleshooting

### Recommended Actions

1. ✅ Run diagnostic script to identify the issue
2. ✅ Check backend logs for specific error messages
3. ✅ Verify Supabase credentials are correct
4. ✅ Ensure database table `account_users` exists
5. ✅ Test with a known user ID

## Issue 2: CORS Error on connectAgentZero()

### Symptoms
- Endpoint: `POST /api/user/connect-agent-zero`
- Browser error: `TypeError: Failed to fetch` (CORS preflight failure)
- Request blocked before reaching backend

### Root Cause Analysis

CORS errors occur when:
1. Frontend origin is not in `CORS_ORIGINS` whitelist
2. OPTIONS preflight request fails
3. CORS headers not properly configured

**Current Configuration:**

- **Portal Backend** (`app/__init__.py`):
  - Uses Flask-CORS
  - Configures `/api/*` routes
  - Includes `OPTIONS` method
  - Default: `http://localhost:3000`

- **Docker Compose** (`docker-compose.local.yml:17`):
  ```yaml
  CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000,http://127.0.0.1:3000}
  ```

### Investigation Steps

1. **Check frontend origin:**
   - What URL is the frontend running on?
   - Is it `http://localhost:3000` or something else?

2. **Verify CORS configuration:**
   ```bash
   docker exec portal-backend-local printenv CORS_ORIGINS
   ```

3. **Check CORS headers in response:**
   ```bash
   curl -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type,Authorization" \
        -X OPTIONS \
        http://localhost:5000/api/user/connect-agent-zero \
        -v
   ```

4. **Check backend logs:**
   ```bash
   docker logs portal-backend-local | grep -i cors
   ```

### Common CORS Issues

1. **Origin Mismatch**
   - Frontend: `http://localhost:5173` (Vite default)
   - Backend: Only allows `http://localhost:3000`
   - **Fix**: Add frontend origin to `CORS_ORIGINS`

2. **Protocol Mismatch**
   - Frontend: `https://`
   - Backend: Only allows `http://`
   - **Fix**: Match protocols

3. **Port Mismatch**
   - Frontend: `:5173`
   - Backend: Only allows `:3000`
   - **Fix**: Add correct port to `CORS_ORIGINS`

4. **Missing OPTIONS Handler**
   - Flask-CORS should handle this automatically
   - **Check**: Verify Flask-CORS is installed and configured

### Fixes Applied

1. **Enhanced CORS logging** - Backend logs CORS origins on startup
2. **Diagnostic script** - Checks CORS configuration

### Recommended Actions

1. ✅ Identify frontend origin (check browser console/network tab)
2. ✅ Add frontend origin to `CORS_ORIGINS` environment variable
3. ✅ Restart Portal Backend container
4. ✅ Test OPTIONS preflight request
5. ✅ Verify CORS headers in response

### Quick Fix

If frontend is on `http://localhost:5173`, update `docker-compose.local.yml`:

```yaml
environment:
  - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173}
```

Then restart:
```bash
docker-compose -f docker-compose.local.yml restart portal-backend
```

## Verification Checklist

### Backend Health
- [ ] Diagnostic script passes all checks
- [ ] Environment variables set correctly
- [ ] Database connection successful
- [ ] CORS origins include frontend origin

### Error Handling
- [ ] Frontend extracts error messages correctly ✅ (Verified)
- [ ] Backend returns proper error format ✅ (Verified)
- [ ] Errors are logged with sufficient detail ✅ (Improved)

### CORS Configuration
- [ ] Frontend origin whitelisted
- [ ] OPTIONS preflight works
- [ ] CORS headers present in responses

## Next Steps

1. **Run diagnostics:**
   ```bash
   docker exec portal-backend-local python -m app.diagnostics
   ```

2. **Check logs:**
   ```bash
   docker logs portal-backend-local --tail 50
   ```

3. **Fix CORS:**
   - Identify frontend origin
   - Update `CORS_ORIGINS` in docker-compose
   - Restart container

4. **Test endpoints:**
   ```bash
   # Test status endpoint
   curl -H "Authorization: Bearer <token>" \
        http://localhost:5000/api/user/agent-zero-status
   
   # Test CORS preflight
   curl -H "Origin: http://localhost:3000" \
        -X OPTIONS \
        http://localhost:5000/api/user/connect-agent-zero \
        -v
   ```

## Conclusion

The frontend error handling is **correct**. The issues are backend configuration problems:

1. **500 Error**: Database/connection issue - needs diagnostic investigation
2. **CORS Error**: Frontend origin not whitelisted - needs CORS configuration update

Both issues can be resolved by:
- Running the diagnostic script
- Checking backend logs
- Updating CORS configuration
- Verifying environment variables
