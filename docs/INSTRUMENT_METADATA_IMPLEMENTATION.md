# Instrument Metadata Implementation

## Overview

This document describes the implementation of the Enhanced Instrument Registration with Profile/Tag Metadata feature for Agent Zero.

## Implementation Summary

The implementation adds profile-based skill assignment to instruments while maintaining backward compatibility and not modifying core Agent Zero profiles.

### Key Features

1. **Central Metadata Registry** (`instruments/metadata.json`)
   - Stores instrument metadata separately from Agent Zero core files
   - Supports profiles, tags, priorities, and custom metadata
   - Backward compatible with existing instruments

2. **API Endpoints**
   - `POST /api/register_instrument` - Register new instruments with metadata
   - `POST /api/instrument_list` - List instruments with filtering
   - `POST /api/instrument_update` - Update instrument metadata
   - `POST /api/profile_instruments` - Manage profile-instrument assignments
   - `POST /api/profile_list` - List available agent profiles

3. **Settings Integration**
   - New "Instruments" section in Agent settings
   - Configurable instrument recall settings
   - "Manage Instruments" button opens instrument manager modal

4. **UI Components**
   - Instrument Manager modal for viewing and managing instruments
   - Profile and tag filtering
   - Enable/disable toggles
   - Edit capabilities (via prompts for now)

5. **Memory Integration**
   - Instruments are enriched with metadata during memory preload
   - Metadata is available for filtering and recall

## File Structure

### New Files Created

```
python/
  helpers/
    instrument_metadata.py        # Core metadata management
    migrate_instruments.py        # Migration script
  api/
    instrument_list.py            # List instruments endpoint
    instrument_update.py          # Update instrument endpoint
    profile_instruments.py        # Profile-instrument management
    profile_list.py              # List profiles endpoint

webui/
  components/
    settings/
      instruments/
        instrument-manager.html          # UI modal
        instrument-manager-store.js      # State management
  css/
    instruments.css               # Styling

instruments/
  metadata.json                   # Central metadata registry

docs/
  api/
    instruments.md                # API documentation
  INSTRUMENT_METADATA_IMPLEMENTATION.md  # This file
```

### Modified Files

```
python/
  api/
    register_instrument.py        # Enhanced with metadata support
  helpers/
    settings.py                   # Added instrument settings
    memory.py                     # Enhanced with metadata enrichment

webui/
  js/
    settings.js                   # Added button handler
```

## Usage Examples

### 1. Register an Instrument with Metadata

```bash
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
    "priority": 2,
    "display_name": "Slack Notifier",
    "category": "Communication"
  }'
```

### 2. List Instruments

```bash
# List all instruments
curl -X POST http://localhost:50080/api/instrument_list \
  -H "Content-Type: application/json" \
  -d '{}'

# List instruments for a specific profile
curl -X POST http://localhost:50080/api/instrument_list \
  -H "Content-Type: application/json" \
  -d '{
    "profile": "developer"
  }'

# Filter by tags
curl -X POST http://localhost:50080/api/instrument_list \
  -H "Content-Type: application/json" \
  -d '{
    "tags": "slack,notification"
  }'
```

### 3. Update Instrument Metadata

```bash
curl -X POST http://localhost:50080/api/instrument_update \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "instrument_id": "n8n.slack_notification",
    "profiles": ["default", "developer", "researcher"],
    "tags": ["slack", "notification", "communication", "urgent"],
    "priority": 1,
    "enabled": true
  }'
```

### 4. Manage Profile Assignments

```bash
# Assign instrument to profile
curl -X POST http://localhost:50080/api/profile_instruments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "profile": "researcher",
    "instrument_id": "n8n.slack_notification",
    "action": "assign"
  }'

# Unassign instrument from profile
curl -X POST http://localhost:50080/api/profile_instruments \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "profile": "researcher",
    "instrument_id": "n8n.slack_notification",
    "action": "unassign"
  }'
```

### 5. Use the UI

1. Open Agent Zero settings
2. Navigate to the "Agent" tab
3. Scroll to the "Instruments" section
4. Click "Manage Instruments" button
5. Use filters to find instruments
6. Toggle enabled/disabled status
7. Click "Edit" to modify profiles, tags, or priority

## Metadata Structure

### Registry Format (`instruments/metadata.json`)

```json
{
  "version": "1.0",
  "instruments": {
    "n8n.slack_notification": {
      "type": "n8n",
      "source_path": "instruments/custom/n8n/workflows/slack_notification.md",
      "profiles": ["default", "developer"],
      "tags": ["slack", "notification", "communication"],
      "priority": 2,
      "enabled": true,
      "metadata": {
        "display_name": "Slack Notifier",
        "category": "Communication"
      }
    }
  }
}
```

### Field Descriptions

- **type**: Instrument type (e.g., "n8n")
- **source_path**: Path to instrument definition file
- **profiles**: Array of profile names this instrument is assigned to
- **tags**: Array of tags for categorization and filtering
- **priority**: Priority level 1-100 (lower = higher priority)
- **enabled**: Boolean indicating if instrument is active
- **metadata**: Additional metadata (display_name, category, etc.)

## Configuration Settings

### New Settings in `settings.py`

```python
# TypedDict additions
instrument_recall_enabled: bool
instrument_recall_interval: int
instrument_recall_max_search: int
instrument_recall_max_result: int
instrument_recall_similarity_threshold: float

# Defaults
instrument_recall_enabled=False         # Off by default
instrument_recall_interval=5            # Every 5 iterations
instrument_recall_max_search=8          # Search up to 8 instruments
instrument_recall_max_result=3          # Show up to 3 instruments
instrument_recall_similarity_threshold=0.4  # 40% similarity minimum
```

### Settings UI Fields

The "Instruments" section in Agent settings provides:
- Enable instrument recall toggle
- Recall interval slider
- Max instruments to search
- Max instruments to show
- Similarity threshold slider
- Manage Instruments button

## Migration

### Migrating Existing Instruments

The migration script (`python/helpers/migrate_instruments.py`) can be used to migrate existing instruments:

```python
from python.helpers.migrate_instruments import run_full_migration

# Run migration
results = run_full_migration(verbose=True)

# Check results
print(f"Migrated: {len(results['migrated'])}")
print(f"Skipped: {len(results['skipped'])}")
print(f"Errors: {len(results['errors'])}")
```

Or run from command line (within Agent Zero environment):

```bash
python -c "from python.helpers.migrate_instruments import run_full_migration; run_full_migration()"
```

### Manual Migration

You can also manually add instruments to `instruments/metadata.json`:

```json
{
  "version": "1.0",
  "instruments": {
    "n8n.your_workflow": {
      "type": "n8n",
      "source_path": "instruments/custom/n8n/workflows/your_workflow.md",
      "profiles": ["default"],
      "tags": ["your", "tags"],
      "priority": 5,
      "enabled": true,
      "metadata": {
        "display_name": "Your Workflow",
        "category": "N8N Workflow"
      }
    }
  }
}
```

## Backward Compatibility

### Guarantees

1. **Existing instruments work without metadata**: Instruments without metadata entries continue to function normally
2. **Existing API calls work**: The `register_instrument` API accepts all new parameters as optional
3. **No core file modifications**: Agent Zero profiles and core extensions remain unchanged
4. **Optional metadata**: System works with or without `metadata.json` file
5. **Graceful degradation**: If metadata loading fails, instruments still load from filesystem

### Testing Backward Compatibility

To verify backward compatibility:

1. **Test without metadata**: Delete `instruments/metadata.json` and verify instruments still load
2. **Test old API calls**: Use old API call format without new parameters
3. **Test memory loading**: Verify memory loads successfully with and without metadata
4. **Test profile switching**: Switch profiles and verify instruments are available

## Future Enhancements

This implementation provides the foundation for:

### Feature 2: Dynamic Instrument Recall
- Per-profile instrument recall
- Context-based instrument suggestions
- Automatic instrument loading based on task

### Feature 3: Profile Management UI
- Visual profile editor
- Drag-and-drop instrument assignment
- Profile cloning and templates

### Additional Enhancements
- Support for non-n8n instrument types
- Instrument versioning
- Usage analytics
- Advanced filtering and search
- Bulk operations
- Instrument templates

## Troubleshooting

### Issue: Instruments not appearing in list

**Solution**: 
1. Check if `instruments/metadata.json` exists
2. Run migration script to populate metadata
3. Check instrument source files exist
4. Verify memory has been reloaded

### Issue: Metadata changes not reflected

**Solution**:
1. Restart Agent Zero to reload memory
2. Or trigger memory reload via API:
   ```python
   await memory.Memory.reload(agent0)
   ```

### Issue: API key required errors

**Solution**:
1. Include API key in request header: `X-API-Key: your-key`
2. Check that API key is configured in Agent Zero settings
3. Some endpoints (list, read) don't require API keys

### Issue: Profile assignments not working

**Solution**:
1. Verify profile exists in `agents/` directory
2. Check metadata.json has correct profile names
3. Ensure at least one profile is assigned (defaults to "default")

## Testing Checklist

- [x] Backward compatibility: Existing instruments load without metadata
- [x] API compatibility: Old API calls work without new parameters
- [x] Memory loading: Doesn't break with missing metadata
- [x] New functionality: Register instrument with profiles/tags
- [x] Filtering: List instruments by profile
- [x] Updates: Update instrument metadata
- [x] UI: View instruments in settings
- [x] Toggles: Enable/disable instruments
- [x] Edge cases: No metadata.json file
- [x] Edge cases: Empty metadata registry
- [ ] Edge cases: Invalid instrument_id (handled with 404)
- [ ] Edge cases: Profile doesn't exist (allowed, creates new profile)
- [ ] Edge cases: Concurrent updates to metadata (file-based locking needed)

## Security Considerations

1. **API Key Protection**: Write operations require API key authentication
2. **Input Validation**: All inputs are validated and sanitized
3. **Path Traversal**: File paths are validated to prevent directory traversal
4. **SQL Injection**: Not applicable (JSON-based storage)
5. **XSS Prevention**: UI properly escapes all user-provided content

## Performance Considerations

1. **Metadata Loading**: Metadata is loaded once during memory preload
2. **File I/O**: Metadata file is read/written only when needed
3. **Memory Impact**: Minimal additional memory usage (metadata is small)
4. **API Performance**: API endpoints are lightweight and fast
5. **UI Responsiveness**: Instrument manager loads asynchronously

## Support

For issues, questions, or contributions related to this feature:

1. Check the [API documentation](./api/instruments.md)
2. Review this implementation guide
3. Check Agent Zero main documentation
4. Open an issue on the project repository

## Version History

- **v1.0** (2025-01-12): Initial implementation
  - Central metadata registry
  - API endpoints
  - Settings integration
  - UI components
  - Memory integration
  - Migration script
  - Documentation

