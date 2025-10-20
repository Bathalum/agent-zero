# Instrument Management API Documentation

This document describes the API endpoints for managing instruments in Agent Zero.

## Overview

The Instrument Management API provides endpoints for:
- Registering new instruments
- Listing instruments with filtering
- Updating instrument metadata
- Managing profile-instrument assignments
- Listing available profiles

## Authentication

Most endpoints require API key authentication. Include the API key in the request header:

```
X-API-Key: your-api-key-here
```

## Endpoints

### 1. Register Instrument

Register a new n8n workflow as an instrument.

**Endpoint:** `POST /api/register_instrument`

**Authentication:** API Key required

**Request Body:**

```json
{
  "workflow_name": "email_workflow",
  "webhook_url": "https://n8n.com/webhook/abc123",
  "description": "Send automated emails",
  "parameters": ["recipient", "template", "data"],
  "profiles": ["default", "researcher"],
  "tags": ["email", "communication"],
  "priority": 5,
  "display_name": "Email Sender",
  "category": "Communication"
}
```

**Parameters:**

- `workflow_name` (required): Unique workflow identifier (alphanumeric with underscores)
- `webhook_url` (required): N8N webhook URL
- `description` (required): Human-readable description
- `parameters` (optional): Array of parameter names for the workflow
- `profiles` (optional): Array of profile names (default: `["default"]`)
- `tags` (optional): Array of tags for categorization
- `priority` (optional): Priority level 1-100 (default: 5, lower = higher priority)
- `display_name` (optional): Display name (defaults to description)
- `category` (optional): Category name (default: "N8N Workflow")

**Response:**

```json
{
  "success": true,
  "message": "Workflow 'email_workflow' registered successfully",
  "workflow_id": "email_workflow",
  "config_path": "/path/to/config.json",
  "description_path": "/path/to/workflow.md",
  "next_steps": [
    "Review the generated instrument description",
    "Test with: python test_workflow.py email_workflow",
    "Restart Agent Zero if memory wasn't reloaded"
  ]
}
```

---

### 2. List Instruments

List registered instruments with optional filtering.

**Endpoint:** `POST /api/instrument_list`

**Authentication:** None required

**Request Body:**

```json
{
  "profile": "researcher",
  "tags": "email,communication",
  "enabled": "true",
  "type": "n8n"
}
```

**Parameters (all optional):**

- `profile`: Filter by profile name
- `tags`: Comma-separated list of tags (matches ANY tag)
- `enabled`: Filter by enabled status ("true" or "false")
- `type`: Filter by instrument type (e.g., "n8n")

**Response:**

```json
{
  "success": true,
  "instruments": [
    {
      "id": "n8n.email_workflow",
      "type": "n8n",
      "display_name": "Email Sender",
      "description": "Send automated emails",
      "profiles": ["default", "researcher"],
      "tags": ["email", "communication"],
      "priority": 5,
      "enabled": true,
      "source_path": "instruments/custom/n8n/workflows/email_workflow.md"
    }
  ],
  "count": 1,
  "filters": {
    "profile": "researcher",
    "tags": ["email", "communication"],
    "enabled": "true",
    "type": "n8n"
  }
}
```

---

### 3. Update Instrument

Update metadata for an existing instrument.

**Endpoint:** `POST /api/instrument_update`

**Authentication:** API Key required

**Request Body:**

```json
{
  "instrument_id": "n8n.email_workflow",
  "profiles": ["default", "researcher", "developer"],
  "tags": ["email", "communication", "automation"],
  "priority": 3,
  "enabled": true,
  "display_name": "Advanced Email Sender",
  "category": "Communication Tools"
}
```

**Parameters:**

- `instrument_id` (required): Unique instrument identifier
- `profiles` (optional): Array of profile names or comma-separated string
- `tags` (optional): Array of tags or comma-separated string
- `priority` (optional): Priority level 1-100
- `enabled` (optional): Boolean or string ("true"/"false")
- `display_name` (optional): Display name for the instrument
- `category` (optional): Category name
- `metadata` (optional): Dictionary of additional metadata

**Response:**

```json
{
  "success": true,
  "message": "Instrument 'n8n.email_workflow' updated successfully",
  "instrument_id": "n8n.email_workflow",
  "updated_fields": ["profiles", "tags", "priority"],
  "instrument": {
    "id": "n8n.email_workflow",
    "type": "n8n",
    "profiles": ["default", "researcher", "developer"],
    "tags": ["email", "communication", "automation"],
    "priority": 3,
    "enabled": true,
    "metadata": {
      "display_name": "Advanced Email Sender",
      "category": "Communication Tools"
    }
  }
}
```

---

### 4. Profile Instruments

Get or modify instruments assigned to a specific profile.

**Endpoint:** `POST /api/profile_instruments`

**Authentication:** API Key required for modifications, optional for listing

**List Instruments for Profile:**

```json
{
  "profile": "researcher"
}
```

**Response:**

```json
{
  "success": true,
  "profile": "researcher",
  "instruments": [
    {
      "id": "n8n.email_workflow",
      "type": "n8n",
      "profiles": ["default", "researcher"],
      "tags": ["email", "communication"],
      "priority": 5,
      "enabled": true
    }
  ],
  "count": 1
}
```

**Assign Instrument to Profile:**

```json
{
  "profile": "researcher",
  "instrument_id": "n8n.email_workflow",
  "action": "assign"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Instrument 'n8n.email_workflow' assigned to profile 'researcher'",
  "instrument_id": "n8n.email_workflow",
  "profile": "researcher",
  "profiles": ["default", "researcher"]
}
```

**Unassign Instrument from Profile:**

```json
{
  "profile": "researcher",
  "instrument_id": "n8n.email_workflow",
  "action": "unassign"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Instrument 'n8n.email_workflow' unassigned from profile 'researcher'",
  "instrument_id": "n8n.email_workflow",
  "profile": "researcher",
  "profiles": ["default"]
}
```

---

### 5. List Profiles

List all available agent profiles.

**Endpoint:** `POST /api/profile_list`

**Authentication:** None required

**Request Body:**

```json
{}
```

**Response:**

```json
{
  "success": true,
  "profiles": [
    {
      "id": "agent0",
      "name": "Agent0",
      "description": "Default agent profile with balanced capabilities"
    },
    {
      "id": "researcher",
      "name": "Researcher",
      "description": "Specialized in research and information gathering"
    },
    {
      "id": "developer",
      "name": "Developer",
      "description": "Specialized in software development tasks"
    }
  ],
  "count": 3
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400` - Bad Request (missing or invalid parameters)
- `401` - Unauthorized (missing or invalid API key)
- `404` - Not Found (instrument or profile not found)
- `500` - Internal Server Error

---

## Examples

### Example 1: Register and Configure an Instrument

```bash
# 1. Register the instrument
curl -X POST http://localhost:50080/api/register_instrument \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "workflow_name": "slack_notification",
    "webhook_url": "https://n8n.example.com/webhook/slack123",
    "description": "Send Slack notifications",
    "parameters": ["channel", "message"],
    "profiles": ["default", "developer"],
    "tags": ["slack", "notification", "communication"],
    "priority": 2
  }'

# 2. Update the instrument
curl -X POST http://localhost:50080/api/instrument_update \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "instrument_id": "n8n.slack_notification",
    "enabled": true,
    "priority": 1
  }'

# 3. List all instruments
curl -X POST http://localhost:50080/api/instrument_list \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Example 2: Profile Management

```bash
# 1. List all profiles
curl -X POST http://localhost:50080/api/profile_list \
  -H "Content-Type: application/json" \
  -d '{}'

# 2. Get instruments for a profile
curl -X POST http://localhost:50080/api/profile_instruments \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "researcher"
  }'

# 3. Assign instrument to profile
curl -X POST http://localhost:50080/api/profile_instruments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "profile": "researcher",
    "instrument_id": "n8n.slack_notification",
    "action": "assign"
  }'
```

---

## Notes

1. **Backward Compatibility**: All new parameters are optional. Existing API calls continue to work without modification.

2. **Default Profile**: Instruments without explicit profile assignment default to `["default"]`.

3. **Priority**: Lower priority numbers indicate higher precedence. Range is 1-100, default is 5.

4. **Tags**: Tags are case-sensitive and should use lowercase with underscores (e.g., `email_notification`).

5. **Metadata Registry**: All instrument metadata is stored in `instruments/metadata.json`.

6. **Memory Integration**: Changes to instrument metadata require memory reload to take effect for dynamic recall.

---

## Future Enhancements

The following features are planned for future releases:

- Instrument versioning
- Usage analytics
- Advanced filtering and search
- Bulk operations
- Instrument templates
- Non-n8n instrument types

