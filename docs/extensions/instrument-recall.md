# Instrument Recall Extension

The Instrument Recall Extension intelligently recalls relevant instruments from memory based on agent profile, task context, and metadata tags. This extension operates on a per-profile basis and integrates seamlessly with Agent Zero's existing memory and extension systems.

## Overview

Similar to how Agent Zero recalls memories during conversation, the Instrument Recall Extension searches the memory database for relevant instruments and injects them into the agent's prompt at appropriate intervals. This makes instruments discoverable and contextually available without manual selection.

## Features

- **Profile-Specific Filtering**: Only recalls instruments assigned to the active agent profile
- **Context-Aware Search**: Uses current task and conversation history to find relevant instruments
- **Priority Sorting**: Instruments with lower priority numbers are preferred
- **Auto-Equip**: Force-include specific instruments regardless of context
- **Exclusion Lists**: Prevent specific instruments from being recalled
- **Tag-Based Filtering**: Filter instruments by metadata tags
- **Configurable Intervals**: Control how often recall happens
- **Similarity Thresholds**: Adjust relevance matching sensitivity

## Installation

### Per-Profile Deployment

The extension is deployed on a per-profile basis, meaning it only affects profiles where you explicitly enable it.

#### Using the Deployment Script

```bash
# Deploy to specific profiles
python -m python.helpers.deploy_instrument_recall --profiles researcher,developer

# Deploy without creating config file
python -m python.helpers.deploy_instrument_recall --profiles researcher --no-config

# Validate deployment
python -m python.helpers.deploy_instrument_recall --profiles researcher --validate

# List available profiles
python -m python.helpers.deploy_instrument_recall --list
```

#### Manual Deployment

1. Copy template files to your profile's extensions directory:
   ```
   python/extensions/profiles/_55_recall_instruments_template.py
   → agents/{profile}/extensions/message_loop_prompts_after/_55_recall_instruments.py
   
   python/extensions/profiles/_91_recall_instruments_wait_template.py
   → agents/{profile}/extensions/message_loop_prompts_after/_91_recall_instruments_wait.py
   ```

2. Create optional configuration file:
   ```
   agents/{profile}/instruments.json
   ```

## Configuration

### Global Settings

Add these settings to your main Agent Zero configuration:

```python
"instrument_recall_enabled": True,           # Enable/disable globally
"instrument_recall_interval": 5,             # Recall every N iterations
"instrument_recall_max_result": 3,           # Max instruments to recall
"instrument_recall_max_search": 8,           # Max instruments to search
"instrument_recall_similarity_threshold": 0.4, # Similarity threshold (0.0-1.0)
```

### Profile-Specific Configuration

Create `agents/{profile}/instruments.json` to override global settings and add profile-specific rules:

```json
{
  "enabled": true,
  "recall_interval": 3,
  "max_instruments": 3,
  "similarity_threshold": 0.35,
  "auto_equip": [
    "n8n.slack_message",
    "n8n.email_workflow"
  ],
  "excluded": [
    "n8n.deprecated_tool"
  ],
  "filters": {
    "tags": ["analysis", "data", "communication"],
    "priority_max": 3
  }
}
```

#### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Override global enable/disable for this profile |
| `recall_interval` | number | How often to recall (every N iterations) |
| `max_instruments` | number | Maximum instruments to include in prompt |
| `similarity_threshold` | number | Minimum similarity score (0.0-1.0) |
| `auto_equip` | array | Instrument IDs to always include |
| `excluded` | array | Instrument IDs to never include |
| `filters.tags` | array | Only include instruments with these tags (OR logic) |
| `filters.priority_max` | number | Only include instruments with priority ≤ this value |

## How It Works

### Recall Process

1. **Interval Check**: Extension runs every N iterations (configurable)

2. **Query Building**: Constructs search query from:
   - Current agent profile
   - User's latest message
   - Recent conversation history (last 2000 chars)

3. **Memory Search**: Searches vector database with filters:
   - Area = "instruments"
   - Enabled = true
   - Profile matches or includes "default"
   - Optional: tag filters, priority filters

4. **Auto-Equip**: Adds force-included instruments to beginning of list

5. **Filtering**: 
   - Removes duplicates (auto-equip takes precedence)
   - Applies exclusion list
   - Sorts by priority (ascending)
   - Limits to max_instruments

6. **Injection**: Formats and injects into agent prompt using existing template

### Extension Timing

The extension runs in two phases:

1. **_55_recall_instruments.py**: Starts async search task
2. **_91_recall_instruments_wait.py**: Waits for task completion

This ensures recall completes before the agent generates its response.

## Examples

### Example 1: Researcher Profile

**Configuration** (`agents/researcher/instruments.json`):
```json
{
  "enabled": true,
  "recall_interval": 3,
  "max_instruments": 3,
  "similarity_threshold": 0.35,
  "filters": {
    "tags": ["analysis", "data", "communication"],
    "priority_max": 3
  }
}
```

**Behavior**:
- Recalls every 3 iterations
- Focuses on analysis and data tools
- Only high-priority instruments (1-3)
- More sensitive matching (0.35 threshold)

### Example 2: Developer Profile

**Configuration** (`agents/developer/instruments.json`):
```json
{
  "enabled": true,
  "recall_interval": 5,
  "max_instruments": 2,
  "similarity_threshold": 0.4,
  "auto_equip": ["n8n.slack_message"],
  "filters": {
    "tags": ["development", "deployment", "communication"]
  }
}
```

**Behavior**:
- Recalls every 5 iterations
- Always includes Slack messaging tool
- Focuses on development and deployment tools
- Limits to 2 instruments to keep prompt concise

## Troubleshooting

### Extension Not Running

1. Check global setting: `instrument_recall_enabled` must be true
2. Verify files exist:
   - `agents/{profile}/extensions/message_loop_prompts_after/_55_recall_instruments.py`
   - `agents/{profile}/extensions/message_loop_prompts_after/_91_recall_instruments_wait.py`
3. Check iteration interval - may need to wait for correct iteration

### No Instruments Recalled

1. Verify instruments exist in memory database
2. Check similarity threshold - may be too high
3. Verify instrument metadata includes correct profile
4. Check exclusion list - instrument may be excluded
5. Verify instrument is enabled in metadata registry

### Wrong Instruments Recalled

1. Adjust similarity threshold
2. Add tag filters to narrow results
3. Use auto_equip for critical instruments
4. Adjust priority values in metadata
5. Add unwanted instruments to exclusion list

### Performance Issues

1. Reduce `recall_interval` if too frequent
2. Lower `max_search` to search fewer candidates
3. Lower `max_instruments` to inject less into prompt
4. Check memory database size and indexing

## Validation

Validate your deployment:

```bash
python -m python.helpers.deploy_instrument_recall --profiles {profile} --validate
```

Expected output:
```
[+] Found: _55_recall_instruments.py
[+] Found: _91_recall_instruments_wait.py
[+] Found: instruments.json
  [+] Valid JSON structure
[SUCCESS] Deployment is valid
```

## Rollback

To remove the extension:

```bash
python -m python.helpers.deploy_instrument_recall --profiles {profile} --rollback
```

Or manually delete:
- `agents/{profile}/extensions/message_loop_prompts_after/_55_recall_instruments.py`
- `agents/{profile}/extensions/message_loop_prompts_after/_91_recall_instruments_wait.py`
- `agents/{profile}/instruments.json` (optional)

## Integration with Instrument Metadata

This extension requires the Instrument Metadata system (Feature 1) to be in place. It relies on:

- **Metadata Registry**: `instruments/metadata.json`
- **Metadata API**: `python/helpers/instrument_metadata.py`
- **Memory Integration**: Instruments stored with enriched metadata in vector DB

See [Instrument Metadata documentation](../instrument-metadata.md) for details.

## Best Practices

1. **Start Conservative**: Begin with higher thresholds and fewer max_instruments
2. **Profile-Specific Rules**: Customize heavily-used profiles first
3. **Use Auto-Equip Sparingly**: Only for mission-critical instruments
4. **Monitor Prompt Size**: Too many instruments can bloat prompts
5. **Test After Changes**: Validate deployment after config changes
6. **Document Custom Configs**: Add comments to instruments.json

## Advanced Usage

### Custom Recall Logic

You can customize the recall extension by editing the deployed file for your profile. The template provides hooks for:

- Custom search query generation
- Additional filtering logic
- Custom sorting algorithms
- Alternative prompt formats

### Multi-Profile Setups

Different profiles can have completely different recall configurations:

```bash
# Researcher: aggressive recall with many instruments
agents/researcher/instruments.json: max_instruments=5, threshold=0.3

# Developer: conservative recall with specific tools
agents/developer/instruments.json: max_instruments=2, auto_equip=['critical_tool']

# Default: fallback to knowledge tool search
agents/default/: (no extension files, uses default behavior)
```

## See Also

- [Instrument Metadata System](../instrument-metadata.md)
- [Profile Configuration](../profiles/instrument-configuration.md)
- [Extension System](../extensibility.md)
- [Memory System](../memory.md)


