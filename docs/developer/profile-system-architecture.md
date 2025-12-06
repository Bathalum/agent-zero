# Profile System Architecture

Technical documentation for developers working with the advanced profile system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [File System Structure](#file-system-structure)
3. [Backend Components](#backend-components)
4. [API Reference](#api-reference)
5. [Frontend Components](#frontend-components)
6. [Data Models](#data-models)
7. [Extension Points](#extension-points)
8. [Security Considerations](#security-considerations)
9. [Migration Guide](#migration-guide)

---

## Architecture Overview

### Design Principles

1. **Minimal Core Changes**: New functionality layered on top of existing system
2. **Backward Compatibility**: Built-in profiles preserved, existing code unaffected
3. **File-Based**: UI reads/writes same files that Agent Zero core uses
4. **Validation-First**: Strong validation prevents corruption
5. **API-Driven**: Clean separation between backend and frontend

### System Layers

```
┌─────────────────────────────────────┐
│         Web UI Components           │
│   (profile-manager, profile-editor) │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│          API Handlers               │
│  (profile_create, profile_delete,   │
│   profile_prompt_*, profile_config_*)│
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│       Helper Modules                │
│ (profile_metadata, profile_validator)│
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│        File System                  │
│      (agents/*/...)                 │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      Agent Zero Core                │
│   (unchanged, loads profiles)       │
└─────────────────────────────────────┘
```

---

## File System Structure

### Profile Directory Layout

```
agents/
├── agent0/                    # Built-in profile
│   ├── _context.md           # Short description
│   └── prompts/
│       └── agent.system.main.role.md
│
├── developer/                 # Built-in profile
│   ├── _context.md
│   ├── prompts/
│   │   ├── agent.system.main.role.md
│   │   └── agent.system.main.communication.md
│   ├── extensions/
│   │   └── message_loop_prompts_after/
│   │       ├── _55_recall_instruments.py
│   │       └── _91_recall_instruments_wait.py
│   └── instruments.json
│
└── custom_profile/            # Custom profile
    ├── _context.md
    ├── profile.json           # Extended metadata
    ├── prompts/
    │   ├── agent.system.main.role.md
    │   ├── agent.system.main.communication.md
    │   └── agent.system.main.environment.md
    ├── extensions/
    │   └── message_loop_prompts_after/
    │       └── _60_my_extension.py
    ├── tools/
    │   └── my_tool.py
    └── instruments.json
```

### File Purposes

| File | Required | Purpose |
|------|----------|---------|
| `_context.md` | ✅ Yes | Short description, first line used in UI |
| `profile.json` | ❌ No | Extended metadata (custom profiles) |
| `prompts/*.md` | ✅ Yes | System prompts for LLM |
| `extensions/**/*.py` | ❌ No | Extension hooks |
| `tools/*.py` | ❌ No | Custom tool implementations |
| `instruments.json` | ❌ No | Instrument recall configuration |

---

## Backend Components

### Helper Modules

#### `python/helpers/profile_metadata.py`

Core utilities for profile management.

**Key Functions:**

```python
def is_builtin_profile(profile_id: str) -> bool:
    """Check if profile is a built-in (read-only)."""
    return profile_id in BUILTIN_PROFILES

def get_profile_metadata(profile_id: str) -> dict[str, Any]:
    """Load profile.json with sensible defaults."""
    # Returns merged defaults + custom metadata

def update_profile_metadata(profile_id: str, metadata: dict[str, Any]) -> bool:
    """Update profile.json, setting modified_at timestamp."""
    # Returns True if successful

def list_available_profiles() -> list[dict[str, Any]]:
    """Get all profiles with enriched metadata."""
    # Returns list of profile dicts

def duplicate_profile(source_id: str, target_id: str, metadata: dict | None) -> bool:
    """Copy profile directory tree."""
    # Returns True if successful

def delete_profile(profile_id: str, force: bool = False) -> tuple[bool, str]:
    """Delete custom profile with safety checks."""
    # Returns (success, error_message)

def create_blank_profile(profile_id: str, metadata: dict | None) -> bool:
    """Create new profile with minimal structure."""
    # Returns True if successful
```

**Constants:**

```python
BUILTIN_PROFILES = ["agent0", "default", "developer", "researcher", "hacker"]
```

#### `python/helpers/profile_validator.py`

Validation logic for profile integrity.

**Key Classes:**

```python
class ProfileValidator:
    def __init__(self, profile_id: str):
        """Initialize validator for a profile."""
        
    def validate_all(self) -> tuple[bool, list[str], list[str]]:
        """Run all validation checks."""
        # Returns (is_valid, errors, warnings)
    
    # Private validation methods:
    # - _validate_profile_exists()
    # - _validate_context_file()
    # - _validate_prompt_files()
    # - _validate_profile_json()
    # - _validate_instruments_json()
    # - _validate_extensions()
    # - _validate_tools()
    # - _validate_no_builtin_conflict()
```

**Utility Functions:**

```python
def validate_profile(profile_id: str) -> tuple[bool, list[str], list[str]]:
    """Convenience function to validate a profile."""

def validate_profile_name(profile_id: str) -> tuple[bool, str]:
    """Validate profile name is acceptable for creation."""
    # Checks: not empty, valid characters, not built-in, doesn't exist
```

---

## API Reference

All API handlers inherit from `ApiHandler` and return either:
- `dict` (success response)
- `Response` (error response with status code)

### Profile Creation

**Endpoint:** `/api/profile_create`

**Handler:** `python/api/profile_create.py`

**Request:**
```json
{
  "profile_id": "my_profile",
  "source_id": "developer",  // optional: profile to duplicate from
  "metadata": {              // optional: custom metadata
    "display_name": "My Profile",
    "description": "Custom profile for..."
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "profile_id": "my_profile",
  "message": "Profile created successfully"
}
```

**Response (Error):**
```json
{
  "error": "Profile name already exists"
}
```

### Profile Deletion

**Endpoint:** `/api/profile_delete`

**Handler:** `python/api/profile_delete.py`

**Request:**
```json
{
  "profile_id": "my_profile"
}
```

**Safety Checks:**
- Cannot delete built-in profiles
- Cannot delete currently active profile
- Returns error if profile doesn't exist

### Prompt Management

**Endpoints:** `/api/profile_prompt_get`, `/api/profile_prompt_set`

**Handlers:** `python/api/profile_prompt_get.py`, `python/api/profile_prompt_set.py`

**Get Request:**
```json
{
  "profile_id": "my_profile",
  "prompt_file": "agent.system.main.role.md"
}
```

**Set Request:**
```json
{
  "profile_id": "my_profile",
  "prompt_file": "agent.system.main.role.md",
  "content": "# Agent Role\n\n..."
}
```

**Security:**
- Path traversal prevention (`..", `/`, `\` rejected)
- Only `.md` files allowed
- Built-in profiles are read-only

### Configuration Management

**Endpoints:** `/api/profile_config_get`, `/api/profile_config_set`

**Handlers:** `python/api/profile_config_get.py`, `python/api/profile_config_set.py`

**Get Response:**
```json
{
  "success": true,
  "config": {
    "enabled": true,
    "recall_interval": 5,
    "max_instruments": 2,
    "similarity_threshold": 0.4,
    "auto_equip": [],
    "excluded": [],
    "filters": {
      "tags": ["development"],
      "priority_max": 5
    }
  },
  "exists": true
}
```

**Set Request:**
```json
{
  "profile_id": "my_profile",
  "config": { /* instruments.json content */ }
}
```

### Extension Management

**Endpoint:** `/api/profile_extensions`

**Handler:** `python/api/profile_extensions.py`

**Actions:**

1. **List:**
```json
{
  "profile_id": "my_profile",
  "action": "list"
}
```

2. **Get:**
```json
{
  "profile_id": "my_profile",
  "action": "get",
  "extension_path": "message_loop_prompts_after/_60_my_ext.py"
}
```

3. **Add:**
```json
{
  "profile_id": "my_profile",
  "action": "add",
  "extension_path": "message_loop_prompts_after/_60_my_ext.py",
  "content": "# Python code..."
}
```

4. **Remove:**
```json
{
  "profile_id": "my_profile",
  "action": "remove",
  "extension_path": "message_loop_prompts_after/_60_my_ext.py"
}
```

### Tool Management

**Endpoint:** `/api/profile_tools`

**Handler:** `python/api/profile_tools.py`

Similar to extension management, with actions: `list`, `get`, `add`, `remove`.

### Import/Export

**Endpoints:** `/api/profile_export`, `/api/profile_import`

**Export:** Returns ZIP file download

**Import Request:**
```json
{
  "profile_id": "new_profile",
  "zip_data": "<base64 encoded ZIP>"
}
```

**ZIP Structure:**
```
profile/
├── _context.md
├── profile.json
├── prompts/
│   └── *.md
├── extensions/
│   └── **/*.py
├── tools/
│   └── *.py
└── instruments.json
```

### Validation

**Endpoint:** `/api/profile_validate`

**Handler:** `python/api/profile_validate.py`

**Response:**
```json
{
  "success": true,
  "is_valid": true,
  "errors": [],
  "warnings": ["Prompt file is empty: agent.system.main.communication.md"]
}
```

---

## Frontend Components

### Profile Store

**File:** `webui/components/profiles/profile-store.js`

**Responsibilities:**
- Centralized state management for profiles
- API communication
- Data caching

**Key Methods:**

```javascript
// Core operations
fetchProfiles()
switchProfile(profileId)
getProfileMetadata(profileId)
updateProfileMetadata(profileId, metadata)

// Advanced operations
createProfile(profileId, sourceId, metadata)
deleteProfile(profileId)
getPrompt(profileId, promptFile)
setPrompt(profileId, promptFile, content)
getConfig(profileId)
setConfig(profileId, config)
manageExtensions(profileId, action, extensionPath, content)
manageTools(profileId, action, toolFile, content)
validateProfile(profileId)
exportProfile(profileId)
importProfile(profileId, zipData)
```

### Profile Manager Component

**File:** `webui/components/profiles/profile-manager.html`

**Features:**
- Grid display of all profiles
- Create/duplicate/delete actions
- Import/export functionality
- Profile switching

**Alpine.js Data Structure:**

```javascript
{
  profiles: [],           // List of profile objects
  currentProfile: null,   // Active profile ID
  loading: false,
  error: null,
  
  // Methods
  loadProfiles(),
  switchToProfile(profileId),
  createBlankProfile(),
  duplicateProfile(profile),
  deleteProfile(profile),
  exportProfileAction(profile),
  importProfile()
}
```

### Profile Editor Component

**File:** `webui/components/profiles/profile-editor.html`

**Tabs:**
1. Basic Info - Metadata, avatar, description
2. Behavior - System prompts (role, communication, environment)
3. Extensions - Extension file management
4. Tools - Custom tool management
5. Skills - Instrument assignment
6. Configuration - Instrument recall settings

**Alpine.js Data Structure:**

```javascript
{
  profileId: null,
  isBuiltin: false,
  metadata: {},
  config: {},
  extensions: [],
  tools: [],
  allInstruments: [],
  assignedInstruments: [],
  activeTab: 'basic',
  selectedPromptFile: 'agent.system.main.role.md',
  promptContent: '',
  promptEditMode: 'markdown',
  promptChanged: false,
  saving: false
}
```

---

## Data Models

### Profile Metadata Schema

```typescript
interface ProfileMetadata {
  display_name: string;          // UI display name
  description: string;           // Short description
  avatar_icon: string;           // Icon identifier
  avatar_color: string;          // Hex color code
  category: string;              // Category (Development, Research, etc.)
  is_custom: boolean;            // True for custom profiles
  base_profile: string | null;  // Source profile if duplicated
  enabled_extensions: string[];  // List of extension paths
  enabled_instruments: string[]; // List of instrument IDs
  instrument_config: {
    enabled: boolean;
    recall_interval: number;
    max_instruments: number;
    similarity_threshold: number;
  };
  created_at: string;            // ISO 8601 timestamp
  modified_at: string;           // ISO 8601 timestamp
}
```

### Instrument Configuration Schema

```typescript
interface InstrumentConfig {
  enabled: boolean;              // Enable instrument recall
  recall_interval: number;       // How often to check (messages)
  max_instruments: number;       // Max to equip at once
  similarity_threshold: number;  // Minimum relevance (0.0-1.0)
  auto_equip: string[];          // Always-equipped instruments
  excluded: string[];            // Never-equipped instruments
  filters: {
    tags: string[];              // Filter by tags
    priority_max: number;        // Max priority level
  };
}
```

---

## Extension Points

### Creating Extensions for Profiles

Extensions are Python files that hook into agent execution flow.

**Extension locations:**
```
extensions/
├── agent_init/              # On agent initialization
├── message_loop_start/      # Start of message loop
├── message_loop_prompts_before/  # Before prompt assembly
├── message_loop_prompts_after/   # After prompt assembly
├── before_main_llm_call/    # Before LLM call
├── response_stream/         # During response streaming
├── tool_execute_before/     # Before tool execution
└── tool_execute_after/      # After tool execution
```

**Extension template:**

```python
from python.helpers.extension import Extension

class MyExtension(Extension):
    async def execute(self, **kwargs):
        """
        Extension execution logic.
        
        Args:
            **kwargs: Context-dependent parameters
                - agent: AgentContext instance
                - prompt: Current prompt (if applicable)
                - tool: Tool being executed (if applicable)
                - result: Tool result (if applicable)
        
        Returns:
            str: Additional content to inject (for prompt extensions)
            or None for non-prompt extensions
        """
        agent = kwargs.get("agent")
        
        # Your logic here
        
        return ""  # Or None
```

### Creating Custom Tools

**Tool template:**

```python
from python.helpers.tool import Tool, Response

class MyTool(Tool):
    
    async def execute(self, **kwargs):
        """
        Tool execution logic.
        
        The docstring becomes the tool description shown to the agent.
        Use clear, concise language explaining what the tool does.
        
        Args:
            **kwargs: Parameters passed by agent
        
        Returns:
            Response: Tool execution result
        """
        # Access tool parameters
        param1 = kwargs.get("param1")
        
        # Your tool logic here
        result = do_something(param1)
        
        # Return result
        return Response(
            message=f"Result: {result}",
            break_loop=False  # Set True to stop agent loop
        )
```

---

## Security Considerations

### Path Traversal Prevention

All file operations validate paths to prevent directory traversal:

```python
# In API handlers
if ".." in filename or "/" in filename or "\\" in filename:
    return Response('{"error": "Invalid path"}', status=400)
```

### Built-in Profile Protection

Built-in profiles are protected at multiple layers:

1. **API Layer:** Check `is_builtin_profile()` before modifications
2. **UI Layer:** Disable edit controls for built-in profiles
3. **Validation Layer:** Reject operations on built-ins

### Input Validation

All inputs are validated:

- Profile names: `^[a-zA-Z0-9_-]+$`
- File extensions: Only `.md` for prompts, `.py` for code
- JSON validation for configuration files
- File size limits (future enhancement)

### Sanitization

- All user-provided content is written directly to files (not executed)
- Extensions and tools are loaded by core system (existing security model)
- No eval/exec on user input

---

## Migration Guide

### From Built-in to Custom Profile

To migrate from a built-in profile:

1. **Duplicate** the built-in profile
2. **Customize** the duplicate
3. **Test** thoroughly
4. **Switch** to custom profile
5. **Monitor** for issues

### Updating Custom Profiles

When Agent Zero updates built-in profiles:

1. **Check** if your custom profile is based on updated built-in
2. **Review** changes in built-in profile
3. **Optionally merge** relevant changes into custom profile
4. **Test** after updates

### Preserving Customizations

Best practices:

- **Document** customizations in profile description
- **Export** profiles regularly
- **Version control** profile directories
- **Track** which built-in version you based on

---

## Development Workflow

### Adding a New API Endpoint

1. Create handler in `python/api/profile_*.py`
2. Inherit from `ApiHandler`
3. Implement `process()` method
4. Set auth requirements
5. The endpoint is auto-registered by `run_ui.py`

**Example:**

```python
from python.helpers.api import ApiHandler, Request, Response

class MyProfileApi(ApiHandler):
    @classmethod
    def requires_auth(cls) -> bool:
        return False
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False
    
    @classmethod
    def requires_api_key(cls) -> bool:
        return False
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            # Your logic
            return {"success": True}
        except Exception as e:
            return Response(
                f'{{"error": "{str(e)}"}}',
                status=500,
                mimetype="application/json"
            )
```

### Adding UI Components

1. Create component in `webui/components/profiles/`
2. Use Alpine.js for reactivity
3. Add styles to `webui/css/profiles.css`
4. Use `fetchApi()` for API calls
5. Use `profileStore` for state management

### Testing Changes

1. **Unit tests**: Test helper functions
2. **API tests**: Test endpoints with various inputs
3. **UI tests**: Manual testing in browser
4. **Integration tests**: Test complete workflows
5. **Edge cases**: Test error conditions

---

## Performance Considerations

### Caching

- Profile metadata cached in frontend store
- File system operations minimized
- Lazy loading of prompt content

### Optimization Tips

- Don't load all profiles on startup
- Use pagination for large profile lists (future)
- Stream large files instead of loading entirely
- Debounce prompt editor saves

---

## Troubleshooting for Developers

### Common Issues

**Issue:** API endpoint not found

**Solution:** Check that handler file is in `python/api/` and follows naming convention.

---

**Issue:** Frontend not updating

**Solution:** Check browser console, verify API responses, check Alpine.js reactivity.

---

**Issue:** Profile validation fails

**Solution:** Check `profile_validator.py` logic, review validation rules.

---

**Issue:** Extensions not loading

**Solution:** Check file paths, Python syntax, agent logs.

---

## Future Enhancements

Potential improvements:

1. **Template Library**: Pre-built profile templates
2. **Profile Marketplace**: Share profiles with community
3. **Version Control**: Track profile changes over time
4. **A/B Testing**: Compare profile performance
5. **Profile Analytics**: Track usage metrics
6. **Bulk Operations**: Manage multiple profiles at once
7. **Profile Inheritance**: Hierarchical profile system
8. **Sub-Agent System**: Profiles as sub-agent definitions

---

## Contributing

When contributing to the profile system:

1. **Follow patterns**: Use existing code as template
2. **Add validation**: Validate all inputs
3. **Error handling**: Handle edge cases gracefully
4. **Documentation**: Update this doc for significant changes
5. **Tests**: Add tests for new functionality
6. **Backward compatibility**: Don't break existing profiles

---

## Resources

- [User Guide](../user/advanced-profile-management.md)
- [Testing Guide](../testing/advanced-profile-testing.md)
- [Agent Zero Core Docs](../README.md)
- [Extension Development](../extensibility.md)
- [Tool Development](../developer/tool-development.md)

---

## API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/profile_list` | POST | List all profiles |
| `/api/profile_create` | POST | Create/duplicate profile |
| `/api/profile_delete` | POST | Delete custom profile |
| `/api/profile_metadata_get` | POST | Get profile metadata |
| `/api/profile_metadata_set` | POST | Update profile metadata |
| `/api/profile_prompt_get` | POST | Read prompt file |
| `/api/profile_prompt_set` | POST | Write prompt file |
| `/api/profile_config_get` | POST | Read instruments.json |
| `/api/profile_config_set` | POST | Write instruments.json |
| `/api/profile_extensions` | POST | Manage extensions |
| `/api/profile_tools` | POST | Manage tools |
| `/api/profile_export` | POST | Export profile as ZIP |
| `/api/profile_import` | POST | Import profile from ZIP |
| `/api/profile_validate` | POST | Validate profile structure |
| `/api/profile_switch` | POST | Switch active profile |

---

**Last Updated:** 2025-10-22  
**Version:** 1.0  
**Authors:** Agent Zero Development Team







