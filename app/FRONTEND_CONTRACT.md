# Portal Backend - Frontend Contract

**This document establishes the formal contract between the Portal Backend API and frontend implementations.**

## Table of Contents

1. [Overview and Architecture](#overview-and-architecture)
2. [Authentication](#authentication)
3. [Endpoint Specifications](#endpoint-specifications)
   - [GET /api/user/agent-zero-status](#get-apiuseragent-zero-status)
   - [GET /api/user/agent-zero-credentials](#get-apiuseragent-zero-credentials)
   - [POST /api/user/connect-agent-zero](#post-apiuserconnect-agent-zero)
   - [DELETE /api/user/agent-zero-credentials](#delete-apiuseragent-zero-credentials)
   - [POST /api/user/get-agent-zero-api-key](#post-apiuserget-agent-zero-api-key)
   - [POST /api/user/update-agent-zero-settings](#post-apiuserupdate-agent-zero-settings)
4. [Error Handling](#error-handling)
5. [Flow Diagrams](#flow-diagrams)
6. [Implementation Examples](#implementation-examples)
7. [Common Patterns](#common-patterns)
8. [Security Considerations](#security-considerations)
9. [Testing Checklist](#testing-checklist)

---

## Overview and Architecture

### Purpose

The Portal Backend API provides a secure bridge between your frontend application and Agent Zero instances. It handles:

- User authentication via Supabase JWT
- Secure credential storage (encrypted Agent Zero passwords)
- Agent Zero API key retrieval and management
- Agent Zero settings updates

### Base URL

The Portal Backend base URL depends on your deployment:

- **Local Development**: `http://localhost:5000`
- **Docker**: `http://localhost:5000` (configurable via `PORTAL_PORT`)
- **Production**: Your deployed backend URL (e.g., `https://api.yourdomain.com`)

All endpoints are prefixed with `/api/user/`.

### CORS Configuration

The Portal Backend requires CORS to be configured for your frontend origin. This is handled via the `CORS_ORIGINS` environment variable in the backend configuration.

**Important**: The frontend origin must be whitelisted in the backend's CORS configuration, or requests will be blocked by the browser.

### Architecture Flow

```
Frontend Application
    ↓ (Supabase JWT Token)
Portal Backend API
    ↓ (Agent Zero Credentials/API Key)
Agent Zero Instance
```

### Design Principles

The Portal Backend follows these design principles:

1. **Format Transformation**: Portal Backend transforms flat dictionaries to the sections format required by Agent Zero. It does not validate, merge, or fetch current settings.

2. **Separation of Concerns**: 
   - **Frontend**: Validates Agent Zero responses, handles UI logic, sends placeholders when preserving values
   - **Portal Backend**: Transforms format (flat dict → sections format), handles authentication, proxies requests
   - **Agent Zero**: Validates settings, processes updates, manages state

3. **Efficiency**: Portal Backend makes a single API call per operation (no pre-fetching of current settings before updates).

---

## Authentication

### Overview

All Portal Backend API endpoints require authentication via **Supabase JWT tokens**. The frontend is responsible for obtaining and managing these tokens.

### Authorization Header

Every request must include an `Authorization` header with the JWT token:

```
Authorization: Bearer <supabase-jwt-token>
```

### Obtaining JWT Tokens

The JWT token is obtained through Supabase authentication. The frontend should:

1. Authenticate users via Supabase Auth (e.g., `supabase.auth.signInWithPassword()`)
2. Extract the JWT token from the session: `session.access_token`
3. Include this token in all Portal Backend API requests

**Example (Supabase JavaScript Client):**

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Sign in user
const { data: { session }, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Extract JWT token
const jwtToken = session.access_token

// Use in API requests
const response = await fetch('http://localhost:5000/api/user/agent-zero-status', {
  headers: {
    'Authorization': `Bearer ${jwtToken}`
  }
})
```

### Token Expiration

JWT tokens have an expiration time. The frontend should:

1. **Monitor token expiration**: Check token expiry before making requests
2. **Refresh tokens**: Use Supabase's `supabase.auth.refreshSession()` to obtain new tokens
3. **Handle 401 errors**: If a request returns 401, refresh the token and retry

### 401 Unauthorized Responses

If the JWT token is missing, invalid, or expired, the backend returns:

```json
{
  "error": "Authentication failed"
}
```

**Status Code**: `401 Unauthorized`

**Action**: Frontend should refresh the token or redirect user to login.

---

## Endpoint Specifications

### GET /api/user/agent-zero-status

Get the current Agent Zero connection status for the authenticated user.

#### Purpose

Check whether the user has connected to an Agent Zero instance and whether an API key is stored.

#### Request

**Method**: `GET`

**Headers**:
```
Authorization: Bearer <supabase-jwt-token>
```

**URL Parameters**: None

**Request Body**: None

#### Response

**Success (200 OK)**:

```json
{
  "has_api_key": true,
  "agent_zero_url": "http://localhost:8080",
  "api_key_retrieved_at": "2025-01-08T12:34:56.789Z"
}
```

**Fields**:
- `has_api_key` (boolean): Whether the user has a stored API key
- `agent_zero_url` (string | null): The Agent Zero instance URL (if connected)
- `api_key_retrieved_at` (string | null): ISO timestamp of when the API key was last retrieved

**Error (500 Internal Server Error)**:

```json
{
  "error": "Failed to retrieve Agent Zero status"
}
```

#### Usage

Use this endpoint to:
- Check if user needs to connect to Agent Zero
- Display connection status in UI
- Determine if settings can be updated

---

### POST /api/user/connect-agent-zero

Connect to an Agent Zero instance by providing credentials and retrieving the API key.

#### Purpose

Initial connection setup for users who haven't connected to Agent Zero yet, or to update connection details.

#### When to Use

- **First-time connection**: User provides Agent Zero URL, username, and password
- **Reconnection**: Update credentials or change Agent Zero instance URL
- **Credential update**: Update stored credentials

#### Request

**Method**: `POST`

**Headers**:
```
Authorization: Bearer <supabase-jwt-token>
Content-Type: application/json
```

**Request Body**:

```json
{
  "agent_zero_url": "http://localhost:8080",
  "username": "myusername",
  "password": "mypassword"
}
```

**Fields**:
- `agent_zero_url` (string, optional): Agent Zero instance URL. Defaults to backend's `AGENT_ZERO_URL` config if not provided. Must start with `http://` or `https://`.
- `username` (string, required): Agent Zero username (from Agent Zero's `AUTH_LOGIN` environment variable)
- `password` (string, required): Agent Zero password (from Agent Zero's `AUTH_PASSWORD` environment variable)

#### Response

**Success (200 OK)**:

```json
{
  "success": true,
  "message": "Successfully connected to Agent Zero and retrieved API key",
  "api_key": "abc123xyz789..."
}
```

**Fields**:
- `success` (boolean): Always `true` on success
- `message` (string): Success message
- `api_key` (string): The Agent Zero API key (MCP Server Token) that was retrieved

**Error - Validation (400 Bad Request)**:

```json
{
  "success": false,
  "message": "Username and password are required"
}
```

Or:

```json
{
  "success": false,
  "message": "Invalid Agent Zero URL"
}
```

**Error - Authentication Failed (401 Unauthorized)**:

```json
{
  "success": false,
  "message": "Authentication failed: Invalid username or password"
}
```

**Error - Connection Failed (503 Service Unavailable)**:

```json
{
  "success": false,
  "message": "Unable to connect to Agent Zero. Please ensure it's running."
}
```

**Error - API Key Not Found (404 Not Found)**:

```json
{
  "success": false,
  "message": "API key not found in Agent Zero settings."
}
```

**Error - Server Error (500 Internal Server Error)**:

```json
{
  "success": false,
  "message": "Failed to store credentials"
}
```

Or:

```json
{
  "success": false,
  "message": "Failed to store API key."
}
```

#### What Happens Internally

1. Backend encrypts and stores the username and password
2. Backend authenticates with Agent Zero using the credentials
3. Backend retrieves the API key from Agent Zero settings
4. Backend stores the API key for future use
5. Future requests can use the stored API key instead of credentials

#### Side Effects

- User's credentials are stored (encrypted) in the database
- User's API key is stored in the database
- User's `agent_zero_url` is stored/updated

---

### POST /api/user/get-agent-zero-api-key

Retrieve or refresh the Agent Zero API key for the authenticated user.

#### Purpose

Get the stored API key, or retrieve it from Agent Zero if not stored (using stored credentials if available).

#### When to Use

- Check if API key exists (check response for `api_key` field)
- Refresh API key if it might have changed
- Retrieve API key after credentials have been stored via `connect-agent-zero`

#### Request

**Method**: `POST`

**Headers**:
```
Authorization: Bearer <supabase-jwt-token>
Content-Type: application/json
```

**Request Body** (optional):

```json
{
  "agent_zero_url": "http://localhost:8080"
}
```

**Fields**:
- `agent_zero_url` (string, optional): Agent Zero instance URL. Defaults to backend's `AGENT_ZERO_URL` config or user's stored URL.

#### Response

**Success - API Key Already Stored (200 OK)**:

```json
{
  "success": true,
  "message": "API key already exists",
  "api_key": "abc123xyz789..."
}
```

**Success - API Key Retrieved (200 OK)**:

```json
{
  "success": true,
  "message": "API key retrieved and stored successfully",
  "api_key": "abc123xyz789..."
}
```

**Error - Validation (400 Bad Request)**:

```json
{
  "success": false,
  "message": "Invalid Agent Zero URL"
}
```

**Error - Authentication Required (401 Unauthorized)**:

If Agent Zero requires authentication and no credentials are stored:

```json
{
  "success": false,
  "message": "Agent Zero requires authentication. Please use /api/user/connect-agent-zero to provide credentials."
}
```

If authentication fails:

```json
{
  "success": false,
  "message": "Invalid username or password"
}
```

**Error - Connection Failed (503 Service Unavailable)**:

```json
{
  "success": false,
  "message": "Unable to connect to Agent Zero. Please ensure it's running."
}
```

**Error - API Key Not Found (404 Not Found)**:

```json
{
  "success": false,
  "message": "API key not found in Agent Zero settings."
}
```

**Error - Server Error (500 Internal Server Error)**:

```json
{
  "success": false,
  "message": "Failed to store API key."
}
```

Or:

```json
{
  "success": false,
  "message": "An unexpected error occurred"
}
```

#### How It Works

1. If API key already stored: Returns it immediately
2. If credentials stored: Uses them to authenticate and retrieve API key
3. If no credentials: Tries to retrieve API key without authentication (only works if Agent Zero has no auth configured)

---

### POST /api/user/update-agent-zero-settings

Update Agent Zero settings using the stored API key.

#### Purpose

Update configuration settings in Agent Zero (e.g., OpenRouter API key, model settings, etc.).

#### Prerequisites

- User must have connected to Agent Zero via `/api/user/connect-agent-zero`
- API key must be stored (check via `/api/user/agent-zero-status`)

#### Request

**Method**: `POST`

**Headers**:
```
Authorization: Bearer <supabase-jwt-token>
Content-Type: application/json
```

**Request Body**:

```json
{
  "settings": {
    "api_key_openrouter": "sk-or-v1-...",
    "chat_model_name": "openai/gpt-4",
    "chat_model_provider": "openrouter",
    "util_model_name": "openai/gpt-4-mini"
  }
}
```

**Fields**:
- `settings` (object, required): Dictionary of Agent Zero setting fields to update. Keys are field IDs from Agent Zero settings.

**Common Setting Fields**:

| Field ID | Type | Description |
|----------|------|-------------|
| `api_key_openrouter` | string | OpenRouter API key |
| `api_key_openai` | string | OpenAI API key |
| `api_key_anthropic` | string | Anthropic API key |
| `chat_model_provider` | string | Chat model provider (e.g., "openrouter", "openai") |
| `chat_model_name` | string | Chat model name (e.g., "openai/gpt-4") |
| `util_model_provider` | string | Utility model provider |
| `util_model_name` | string | Utility model name |
| `embed_model_provider` | string | Embedding model provider |
| `embed_model_name` | string | Embedding model name |

**Note**: Only include fields you want to update. Fields not included remain unchanged.

#### Response

**Success (200 OK)**:

```json
{
  "success": true,
  "message": "Settings updated successfully"
}
```

**Error - Validation (400 Bad Request)**:

```json
{
  "success": false,
  "message": "Settings object is required"
}
```

**Error - Not Connected (404 Not Found)**:

```json
{
  "success": false,
  "message": "Agent Zero API key not found. Please connect to Agent Zero first."
}
```

**Error - Authentication Failed (401 Unauthorized)**:

```json
{
  "success": false,
  "message": "Authentication failed: Invalid API key. Please reconnect to Agent Zero."
}
```

**Error - Connection Failed (503 Service Unavailable)**:

```json
{
  "success": false,
  "message": "Unable to connect to Agent Zero. Please ensure it's running."
}
```

**Error - Server Error (500 Internal Server Error)**:

```json
{
  "success": false,
  "message": "Error updating settings: <error details>"
}
```

Or:

```json
{
  "success": false,
  "message": "An unexpected error occurred"
}
```

#### Important Notes

- The API key stored from initial connection is used automatically
- Settings are updated in Agent Zero immediately
- **Partial Updates**: Only fields included in the `settings` object will be updated. Fields not included remain unchanged.
- Field IDs must match exactly (case-sensitive)
- **Preserving Existing Values**: To preserve an existing API key or password without changing it, send the placeholder value `"************"` for that field. Agent Zero will skip updating fields with this placeholder.

#### How Partial Updates Work

The Portal Backend transforms your flat dictionary to the sections format required by Agent Zero. Agent Zero processes only the fields you send:

- **Fields you include**: Will be updated with the new value (or preserved if value is `"************"`)
- **Fields you don't include**: Remain completely unchanged
- **New fields**: Can be added by including them in the settings object

**Example - Updating only one API key while preserving others:**

```json
{
  "settings": {
    "api_key_openai": "sk-new-key-here",
    "api_key_anthropic": "************"
  }
}
```

In this example:
- `api_key_openai` will be updated to the new value
- `api_key_anthropic` will be preserved (not changed)
- All other API keys and settings remain unchanged

**Example - Clearing a field:**

```json
{
  "settings": {
    "api_key_openai": ""
  }
}
```

Sending an empty string `""` will clear/remove the API key.

#### Frontend Responsibilities

The frontend is responsible for:

1. **Validation**: Validate Agent Zero responses (from `/api/settings_get`) before using them. Portal Backend acts as a pass-through and does not validate Agent Zero's response structure.

2. **Sending Placeholders**: When preserving existing values (especially API keys), explicitly include the field with value `"************"` in your update request.

3. **Field Selection**: Only include fields that have been modified by the user. Unchanged fields should either:
   - Be omitted (to preserve existing value), OR
   - Include placeholder `"************"` (to explicitly preserve)

4. **Error Handling**: Handle validation errors if Agent Zero returns malformed data structures.

---

### GET /api/user/agent-zero-credentials

Retrieve stored Agent Zero credentials for the authenticated user.

#### Purpose

Get the stored username, password, and Agent Zero URL. Useful for pre-filling connection forms or displaying connection details.

#### When to Use

- Pre-fill connection form with stored credentials
- Display current connection details to user
- Verify what credentials are stored

#### Request

**Method**: `GET`

**Headers**:
```
Authorization: Bearer <supabase-jwt-token>
```

**URL Parameters**: None

**Request Body**: None

#### Response

**Success (200 OK)**:

```json
{
  "username": "admin",
  "password": "decrypted_password",
  "agent_zero_url": "http://localhost:8080"
}
```

**Fields**:
- `username` (string): Stored Agent Zero username
- `password` (string): Decrypted Agent Zero password (returned for form pre-filling)
- `agent_zero_url` (string): Stored Agent Zero instance URL

**Error - Not Found (404 Not Found)**:

```json
{
  "error": "Agent Zero credentials not found"
}
```

**Error - Server Error (500 Internal Server Error)**:

```json
{
  "error": "Failed to retrieve Agent Zero credentials"
}
```

#### Security Note

The password is returned decrypted because:
- Only the authenticated user can access their own credentials
- Credentials are encrypted at rest in the database
- User already knows their password (they entered it)
- Necessary for frontend to pre-fill connection forms

#### Usage

Use this endpoint to:
- Pre-fill connection form when user wants to update credentials
- Display current connection details
- Verify stored credentials before attempting connection

---

### DELETE /api/user/agent-zero-credentials

Clear stored Agent Zero credentials and API key for the authenticated user.

#### Purpose

Disconnect from Agent Zero by removing all stored credentials and API key. This effectively "disconnects" the user from their Agent Zero instance.

#### When to Use

- User wants to disconnect from Agent Zero
- User wants to clear stored credentials
- User wants to switch to a different Agent Zero instance
- Security: User wants to remove credentials from system

#### Request

**Method**: `DELETE`

**Headers**:
```
Authorization: Bearer <supabase-jwt-token>
```

**URL Parameters**: None

**Request Body**: None

#### Response

**Success (200 OK)**:

```json
{
  "success": true,
  "message": "Agent Zero credentials and API key cleared successfully"
}
```

**Fields**:
- `success` (boolean): Always `true` on success
- `message` (string): Success message

**Error - Server Error (500 Internal Server Error)**:

```json
{
  "success": false,
  "message": "Failed to clear Agent Zero credentials"
}
```

#### What Gets Cleared

The following fields are set to NULL in the database:
- `agent_zero_username`
- `agent_zero_password_encrypted`
- `agent_zero_api_key`
- `agent_zero_api_key_retrieved_at`

**Note**: `agent_zero_url` is preserved (useful for reconnection).

#### Side Effects

- User's credentials are removed from database
- User's API key is removed from database
- User will need to reconnect to use Agent Zero features
- Settings updates will no longer work (requires API key)

#### Usage

Use this endpoint to:
- Implement "Disconnect" or "Clear Credentials" button
- Allow users to switch Agent Zero instances
- Provide security option to remove stored credentials

---

## Error Handling

### Standard Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "message": "Human-readable error message"
}
```

For endpoints that don't use the `success` field (like `/agent-zero-status`):

```json
{
  "error": "Error message"
}
```

### Status Codes

| Status Code | Meaning | When It Occurs | Action |
|------------|---------|----------------|--------|
| `200 OK` | Success | Request completed successfully | Process response data |
| `400 Bad Request` | Validation Error | Invalid request data (missing required fields, invalid URL format, etc.) | Fix request data and retry |
| `401 Unauthorized` | Authentication Failed | Invalid JWT token, or Agent Zero authentication failed | Refresh JWT token or reconnect to Agent Zero |
| `404 Not Found` | Resource Not Found | API key not found in Agent Zero settings, or user not connected | Connect to Agent Zero first |
| `500 Internal Server Error` | Server Error | Database error, unexpected server error | Show error to user, log for debugging |
| `503 Service Unavailable` | Connection Failed | Cannot connect to Agent Zero instance | Check Agent Zero is running, verify URL |

### Error Handling Best Practices

1. **Always check response status**: Don't assume success based on response body alone
2. **Handle 401 errors**: Refresh JWT token and retry
3. **Show user-friendly messages**: Use the `message` field from error responses
4. **Log errors for debugging**: Include full error details in logs
5. **Don't retry 400 errors**: Validation errors require user action
6. **Retry 503 errors**: Connection failures might be temporary

### Example Error Handling

```javascript
async function callAPI(endpoint, options) {
  try {
    const response = await fetch(endpoint, options)
    const data = await response.json()
    
    if (!response.ok) {
      // Handle specific status codes
      if (response.status === 401) {
        // Refresh token and retry
        await refreshToken()
        return callAPI(endpoint, options) // Retry
      }
      
      if (response.status === 400) {
        // Validation error - show to user
        throw new Error(data.message || 'Invalid request')
      }
      
      // Other errors
      throw new Error(data.message || `Error: ${response.status}`)
    }
    
    return data
  } catch (error) {
    console.error('API call failed:', error)
    throw error
  }
}
```

---

## Flow Diagrams

### Initial Connection Flow (First Time Setup)

```
User enters credentials
    ↓
POST /api/user/connect-agent-zero
    ↓
Backend stores credentials (encrypted)
    ↓
Backend authenticates with Agent Zero
    ↓
Backend retrieves API key from Agent Zero
    ↓
Backend stores API key
    ↓
Success: API key returned to frontend
```

### Settings Update Flow

```
User updates settings in UI
    ↓
POST /api/user/update-agent-zero-settings
    ↓
Backend retrieves stored API key
    ↓
Backend authenticates with Agent Zero using API key
    ↓
Backend updates settings in Agent Zero
    ↓
Success: Settings updated
```

### API Key Refresh Flow

```
User needs to refresh API key
    ↓
POST /api/user/get-agent-zero-api-key
    ↓
Backend checks if API key exists
    ├─ Yes → Return stored API key
    └─ No → Check for stored credentials
            ├─ Yes → Authenticate and retrieve API key
            └─ No → Try unauthenticated (if Agent Zero has no auth)
    ↓
Backend stores API key (if retrieved)
    ↓
Success: API key returned
```

---

## Implementation Examples

### React Example

```javascript
import { useState, useEffect } from 'react'
import { useSupabaseClient } from '@supabase/supabase-js'

const AgentZeroConnection = () => {
  const supabase = useSupabaseClient()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState(null)

  // Check connection status on mount
  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const response = await fetch('http://localhost:5000/api/user/agent-zero-status', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setStatus(data)
      }
    } catch (err) {
      console.error('Failed to check status:', err)
    }
  }

  const connect = async (url, username, password) => {
    setLoading(true)
    setError(null)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        throw new Error('Not authenticated')
      }

      const response = await fetch('http://localhost:5000/api/user/connect-agent-zero', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          agent_zero_url: url,
          username,
          password
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || 'Connection failed')
      }

      // Success - refresh status
      await checkStatus()
      alert('Successfully connected!')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const updateSettings = async (settings) => {
    setLoading(true)
    setError(null)

    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        throw new Error('Not authenticated')
      }

      const response = await fetch('http://localhost:5000/api/user/update-agent-zero-settings', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.message || 'Update failed')
      }

      alert('Settings updated successfully!')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {error && <div className="error">{error}</div>}
      {loading && <div>Loading...</div>}
      
      {status && (
        <div>
          <p>Status: {status.has_api_key ? 'Connected' : 'Not Connected'}</p>
          {status.agent_zero_url && <p>URL: {status.agent_zero_url}</p>}
        </div>
      )}

      {/* Connection form would go here */}
    </div>
  )
}

export default AgentZeroConnection
```

### Vanilla JavaScript Example

```javascript
class PortalBackendClient {
  constructor(baseURL, getToken) {
    this.baseURL = baseURL
    this.getToken = getToken // Function that returns JWT token
  }

  async request(endpoint, options = {}) {
    const token = await this.getToken()
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.message || data.error || `HTTP ${response.status}`)
    }

    return data
  }

  async getStatus() {
    return this.request('/api/user/agent-zero-status', {
      method: 'GET'
    })
  }

  async connectAgentZero(url, username, password) {
    return this.request('/api/user/connect-agent-zero', {
      method: 'POST',
      body: JSON.stringify({
        agent_zero_url: url,
        username,
        password
      })
    })
  }

  async updateSettings(settings) {
    return this.request('/api/user/update-agent-zero-settings', {
      method: 'POST',
      body: JSON.stringify({ settings })
    })
  }

  async getAPIKey(url = null) {
    const body = url ? { agent_zero_url: url } : {}
    return this.request('/api/user/get-agent-zero-api-key', {
      method: 'POST',
      body: JSON.stringify(body)
    })
  }

  async getCredentials() {
    return this.request('/api/user/agent-zero-credentials', {
      method: 'GET'
    })
  }

  async deleteCredentials() {
    return this.request('/api/user/agent-zero-credentials', {
      method: 'DELETE'
    })
  }
}

// Usage
const client = new PortalBackendClient(
  'http://localhost:5000',
  async () => {
    // Get JWT token from Supabase
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token
  }
)

// Check status
try {
  const status = await client.getStatus()
  console.log('Connected:', status.has_api_key)
} catch (error) {
  console.error('Error:', error.message)
}

// Connect to Agent Zero
try {
  const result = await client.connectAgentZero(
    'http://localhost:8080',
    'myusername',
    'mypassword'
  )
  console.log('API Key:', result.api_key)
} catch (error) {
  console.error('Connection failed:', error.message)
}

// Update settings
try {
  await client.updateSettings({
    api_key_openrouter: 'sk-or-v1-...',
    chat_model_name: 'openai/gpt-4'
  })
  console.log('Settings updated')
} catch (error) {
  console.error('Update failed:', error.message)
}

// Get stored credentials
try {
  const credentials = await client.getCredentials()
  console.log('Username:', credentials.username)
  console.log('URL:', credentials.agent_zero_url)
  // Password is also available but should be handled securely
} catch (error) {
  if (error.message.includes('not found')) {
    console.log('No credentials stored')
  } else {
    console.error('Error:', error.message)
  }
}

// Delete credentials (disconnect)
try {
  await client.deleteCredentials()
  console.log('Disconnected from Agent Zero')
} catch (error) {
  console.error('Disconnect failed:', error.message)
}
```

### TypeScript Types Example

```typescript
interface AgentZeroStatus {
  has_api_key: boolean
  agent_zero_url: string | null
  api_key_retrieved_at: string | null
}

interface ConnectAgentZeroRequest {
  agent_zero_url?: string
  username: string
  password: string
}

interface ConnectAgentZeroResponse {
  success: boolean
  message: string
  api_key?: string
}

interface UpdateSettingsRequest {
  settings: Record<string, any>
}

interface UpdateSettingsResponse {
  success: boolean
  message: string
}

interface ErrorResponse {
  success?: false
  error?: string
  message?: string
}

class PortalBackendClient {
  constructor(
    private baseURL: string,
    private getToken: () => Promise<string | null>
  ) {}

  async getStatus(): Promise<AgentZeroStatus> {
    return this.request<AgentZeroStatus>('/api/user/agent-zero-status', {
      method: 'GET'
    })
  }

  async connectAgentZero(
    request: ConnectAgentZeroRequest
  ): Promise<ConnectAgentZeroResponse> {
    return this.request<ConnectAgentZeroResponse>(
      '/api/user/connect-agent-zero',
      {
        method: 'POST',
        body: JSON.stringify(request)
      }
    )
  }

  async updateSettings(
    request: UpdateSettingsRequest
  ): Promise<UpdateSettingsResponse> {
    return this.request<UpdateSettingsResponse>(
      '/api/user/update-agent-zero-settings',
      {
        method: 'POST',
        body: JSON.stringify(request)
      }
    )
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getToken()
    if (!token) {
      throw new Error('Not authenticated')
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    })

    const data = await response.json()

    if (!response.ok) {
      const error = data as ErrorResponse
      throw new Error(error.message || error.error || `HTTP ${response.status}`)
    }

    return data as T
  }
}
```

---

## Common Patterns

### Checking Connection Status Before Operations

Always check if the user is connected before allowing settings updates:

```javascript
async function canUpdateSettings() {
  const status = await client.getStatus()
  return status.has_api_key
}

// Before updating settings
if (!(await canUpdateSettings())) {
  alert('Please connect to Agent Zero first')
  return
}

await client.updateSettings({ ... })
```

### Pre-filling Connection Form

Retrieve stored credentials to pre-fill the connection form:

```javascript
async function prefillConnectionForm() {
  try {
    const credentials = await client.getCredentials()
    setUrl(credentials.agent_zero_url)
    setUsername(credentials.username)
    setPassword(credentials.password)
  } catch (error) {
    if (error.message.includes('not found')) {
      // No credentials stored - form stays empty
      return
    }
    console.error('Error loading credentials:', error)
  }
}
```

### Disconnecting from Agent Zero

Clear all stored credentials and API key:

```javascript
async function disconnectAgentZero() {
  if (!confirm('Are you sure you want to disconnect? This will clear all stored credentials.')) {
    return
  }

  try {
    await client.deleteCredentials()
    showNotification('Disconnected from Agent Zero', 'success')
    // Refresh status
    await checkStatus()
  } catch (error) {
    showNotification('Failed to disconnect: ' + error.message, 'error')
  }
}
```

### Handling Expired Tokens

Implement automatic token refresh:

```javascript
let tokenRefreshPromise = null

async function getTokenWithRefresh() {
  const { data: { session } } = await supabase.auth.getSession()
  
  if (!session) {
    throw new Error('Not authenticated')
  }

  // Check if token expires soon (within 5 minutes)
  const expiresAt = session.expires_at * 1000
  const now = Date.now()
  const fiveMinutes = 5 * 60 * 1000

  if (expiresAt - now < fiveMinutes) {
    // Refresh token
    if (!tokenRefreshPromise) {
      tokenRefreshPromise = supabase.auth.refreshSession()
    }
    const { data } = await tokenRefreshPromise
    tokenRefreshPromise = null
    return data.session.access_token
  }

  return session.access_token
}
```

### Storing Agent Zero URL in Frontend State

Once connected, store the URL for future requests:

```javascript
const [agentZeroURL, setAgentZeroURL] = useState(null)

useEffect(() => {
  client.getStatus().then(status => {
    if (status.agent_zero_url) {
      setAgentZeroURL(status.agent_zero_url)
    }
  })
}, [])

// Use when updating settings
await client.updateSettings({ ... }) // Uses stored URL automatically
```

### Form Validation

Validate inputs before sending requests:

```javascript
function validateConnectionForm(url, username, password) {
  const errors = []

  if (!url || !url.startsWith('http://') && !url.startsWith('https://')) {
    errors.push('URL must start with http:// or https://')
  }

  if (!username || username.trim().length === 0) {
    errors.push('Username is required')
  }

  if (!password || password.length === 0) {
    errors.push('Password is required')
  }

  return errors
}

// Before submitting
const errors = validateConnectionForm(url, username, password)
if (errors.length > 0) {
  setFormErrors(errors)
  return
}
```

### User Feedback Patterns

Provide clear feedback for all operations:

```javascript
async function handleConnect() {
  setLoading(true)
  setError(null)

  try {
    const result = await client.connectAgentZero(url, username, password)
    // Success feedback
    showNotification('Successfully connected to Agent Zero!', 'success')
    // Clear form
    setUrl('')
    setUsername('')
    setPassword('')
  } catch (err) {
    // Error feedback
    if (err.message.includes('Authentication failed')) {
      setError('Invalid username or password')
    } else if (err.message.includes('Unable to connect')) {
      setError('Cannot connect to Agent Zero. Please check the URL and ensure it\'s running.')
    } else {
      setError(err.message)
    }
  } finally {
    setLoading(false)
  }
}
```

---

## Security Considerations

### JWT Token Security

- **Never store JWT tokens in localStorage**: Use secure storage (httpOnly cookies if possible, or sessionStorage)
- **Always use HTTPS in production**: JWT tokens must be transmitted over encrypted connections
- **Monitor token expiration**: Refresh tokens before they expire to avoid 401 errors
- **Handle token refresh errors**: If refresh fails, redirect user to login

### Credential Handling

- **Credentials sent only once**: During initial connection via `/connect-agent-zero`
- **Credentials never returned**: Backend never returns passwords in responses
- **Encrypted storage**: Backend encrypts passwords before storing in database
- **No credential exposure**: Frontend should never display or log credentials

### API Key Security

- **API keys stored in backend only**: Frontend never stores Agent Zero API keys
- **API keys not exposed**: Backend uses API keys internally; frontend never sees them (except in initial connection response)
- **Rotate keys if compromised**: If credentials are compromised, user should update Agent Zero password and reconnect

### HTTPS Requirements

- **Always use HTTPS in production**: All API calls must use HTTPS
- **Validate SSL certificates**: Don't disable certificate validation
- **Use secure origins**: CORS origins should be HTTPS URLs in production

### Input Validation

- **Validate URLs**: Ensure URLs start with `http://` or `https://`
- **Sanitize inputs**: Don't trust user input; validate on frontend and rely on backend validation
- **Prevent XSS**: Never inject user input directly into DOM without sanitization

---

## Testing Checklist

Use this checklist to verify your frontend implementation:

### Authentication

- [ ] JWT token is included in all requests
- [ ] Token refresh works when token expires
- [ ] 401 errors are handled correctly
- [ ] User is redirected to login when authentication fails

### GET /api/user/agent-zero-status

- [ ] Status check works correctly
- [ ] Displays connection status in UI
- [ ] Handles 500 errors gracefully

### POST /api/user/connect-agent-zero

- [ ] Connection form validates inputs
- [ ] Success response is handled correctly
- [ ] API key is not displayed in UI (or shown only once with warning)
- [ ] 400 errors (validation) are shown to user
- [ ] 401 errors (auth failed) are shown to user
- [ ] 503 errors (connection failed) are shown to user
- [ ] 404 errors (API key not found) are shown to user
- [ ] 500 errors (server error) are shown to user

### POST /api/user/get-agent-zero-api-key

- [ ] Retrieves API key if already stored
- [ ] Uses stored credentials if no API key exists
- [ ] Handles case where no credentials are stored
- [ ] Handles all error cases correctly

### POST /api/user/update-agent-zero-settings

- [ ] Checks connection status before allowing updates
- [ ] Validates settings object structure
- [ ] Shows success message after update
- [ ] Handles 404 (not connected) error
- [ ] Handles 401 (invalid API key) error
- [ ] Handles 503 (connection failed) error
- [ ] Handles 500 (server error) error

### GET /api/user/agent-zero-credentials

- [ ] Retrieves stored credentials correctly
- [ ] Returns 404 when no credentials exist
- [ ] Password is decrypted and returned
- [ ] Handles 500 errors gracefully
- [ ] Can be used to pre-fill connection form

### DELETE /api/user/agent-zero-credentials

- [ ] Clears credentials successfully
- [ ] Clears API key successfully
- [ ] Returns success message
- [ ] Handles 500 errors gracefully
- [ ] User can reconnect after deletion
- [ ] Status check reflects disconnected state after deletion

### Error Handling

- [ ] All error responses are handled
- [ ] User-friendly error messages are displayed
- [ ] Errors are logged for debugging
- [ ] 401 errors trigger token refresh
- [ ] Network errors are handled gracefully

### Security

- [ ] JWT tokens are stored securely
- [ ] HTTPS is used in production
- [ ] Credentials are never logged
- [ ] API keys are not exposed unnecessarily
- [ ] Input validation is implemented

### User Experience

- [ ] Loading states are shown during requests
- [ ] Success feedback is provided
- [ ] Error messages are clear and actionable
- [ ] Forms are validated before submission
- [ ] Connection status is displayed

---

## Summary

This contract defines the Portal Backend API interface for frontend applications. Key points:

1. **Authentication**: All requests require Supabase JWT tokens in the `Authorization` header
2. **Endpoints**: Four endpoints for status, connection, API key retrieval, and settings updates
3. **Error Handling**: Comprehensive error responses with clear messages
4. **Security**: Credentials and API keys are handled securely by the backend
5. **Implementation**: Use the provided examples as a starting point

**The backend is the source of truth for all API specifications. Frontend implementations must conform to this contract.**

---

**Contract Version**: 1.0.0  
**Last Updated**: 2025-01-08  
**Backend Version**: Portal Backend v1.0
