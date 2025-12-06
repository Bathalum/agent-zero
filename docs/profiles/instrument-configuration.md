# Profile Instrument Configuration

This document describes how to configure instrument recall behavior for specific agent profiles using the `instruments.json` configuration file.

## Overview

Each agent profile can have its own `instruments.json` file that controls how instruments are recalled and presented to that profile. This allows you to:

- Customize recall behavior per profile
- Override global settings
- Define profile-specific instrument preferences
- Control which instruments are available to each profile

## Configuration File Location

```
agents/{profile}/instruments.json
```

Examples:
- `agents/researcher/instruments.json`
- `agents/developer/instruments.json`
- `agents/custom_profile/instruments.json`

## Configuration Schema

### Complete Example

```json
{
  "enabled": true,
  "recall_interval": 5,
  "max_instruments": 3,
  "similarity_threshold": 0.4,
  "auto_equip": [
    "n8n.slack_message",
    "n8n.email_workflow"
  ],
  "excluded": [
    "n8n.deprecated_tool",
    "n8n.experimental_feature"
  ],
  "filters": {
    "tags": ["communication", "data", "analysis"],
    "priority_max": 3
  }
}
```

### Field Definitions

#### `enabled`
- **Type**: `boolean`
- **Required**: No
- **Default**: Uses global `instrument_recall_enabled` setting
- **Description**: Enable or disable instrument recall for this profile, overriding global setting

```json
{
  "enabled": true  // Enable for this profile even if disabled globally
}
```

#### `recall_interval`
- **Type**: `number` (integer)
- **Required**: No
- **Default**: Uses global `instrument_recall_interval` setting
- **Description**: Number of iterations between recall attempts. Lower = more frequent.

```json
{
  "recall_interval": 3  // Recall every 3 iterations
}
```

**Recommendations**:
- Research profiles: 3-5 (frequent recall for dynamic tasks)
- Stable profiles: 5-10 (less frequent for consistent workflows)

#### `max_instruments`
- **Type**: `number` (integer)
- **Required**: No
- **Default**: Uses global `instrument_recall_max_result` setting
- **Description**: Maximum number of instruments to include in agent prompt

```json
{
  "max_instruments": 3  // Include up to 3 instruments
}
```

**Considerations**:
- More instruments = better coverage but larger prompts
- Fewer instruments = focused but may miss relevant tools
- Consider token limits and model context size

#### `similarity_threshold`
- **Type**: `number` (float, 0.0-1.0)
- **Required**: No
- **Default**: Uses global `instrument_recall_similarity_threshold` setting
- **Description**: Minimum similarity score for including an instrument

```json
{
  "similarity_threshold": 0.35  // Lower = more permissive
}
```

**Guidelines**:
- `0.2-0.3`: Very permissive, may include tangentially related instruments
- `0.3-0.4`: Balanced, good for most use cases
- `0.4-0.5`: Strict, only very relevant instruments
- `0.5+`: Very strict, may miss relevant instruments

#### `auto_equip`
- **Type**: `array` of `string`
- **Required**: No
- **Default**: `[]` (empty)
- **Description**: Instrument IDs to always include, regardless of search results

```json
{
  "auto_equip": [
    "n8n.slack_message",
    "n8n.critical_tool"
  ]
}
```

**Use Cases**:
- Critical communication tools (Slack, email)
- Profile-essential instruments
- Frequently-used utilities
- Emergency/fallback tools

**Notes**:
- Auto-equipped instruments appear first (highest priority)
- Still counts toward `max_instruments` limit
- Instruments must exist and be enabled in metadata registry

#### `excluded`
- **Type**: `array` of `string`
- **Required**: No
- **Default**: `[]` (empty)
- **Description**: Instrument IDs to never include for this profile

```json
{
  "excluded": [
    "n8n.deprecated_tool",
    "n8n.admin_only_feature"
  ]
}
```

**Use Cases**:
- Deprecated instruments still in database
- Tools inappropriate for profile
- Experimental features
- Security-restricted tools

#### `filters`
- **Type**: `object`
- **Required**: No
- **Default**: `{}` (no additional filters)
- **Description**: Additional filtering criteria for instrument selection

##### `filters.tags`
- **Type**: `array` of `string`
- **Logic**: OR (instrument must have at least one matching tag)
- **Description**: Only include instruments with these tags

```json
{
  "filters": {
    "tags": ["analysis", "data", "communication"]
  }
}
```

**Example Tags**:
- `analysis`: Data analysis tools
- `communication`: Messaging/notification tools
- `deployment`: CI/CD and deployment tools
- `development`: Coding and dev tools
- `data`: Data processing tools
- `monitoring`: Monitoring and alerting tools

##### `filters.priority_max`
- **Type**: `number` (integer) or `null`
- **Description**: Only include instruments with priority ≤ this value

```json
{
  "filters": {
    "priority_max": 3  // Only priority 1, 2, or 3
  }
}
```

**Priority Recommendations**:
- `1`: Critical, always-useful instruments
- `2`: Very useful, frequently needed
- `3`: Useful for specific tasks
- `4-5`: Specialized or situational
- `6+`: Rarely used or experimental

## Profile Examples

### Researcher Profile

Focus on data analysis, communication, and high-priority tools.

```json
{
  "enabled": true,
  "recall_interval": 3,
  "max_instruments": 3,
  "similarity_threshold": 0.35,
  "auto_equip": [],
  "excluded": [
    "n8n.deploy_production",
    "n8n.code_review"
  ],
  "filters": {
    "tags": ["analysis", "data", "communication", "visualization"],
    "priority_max": 3
  }
}
```

**Characteristics**:
- Frequent recall (every 3 iterations)
- Permissive threshold (0.35) for broad discovery
- Excludes development-specific tools
- Focuses on analysis and data tags

### Developer Profile

Focus on development, deployment, and code tools with critical communication.

```json
{
  "enabled": true,
  "recall_interval": 5,
  "max_instruments": 2,
  "similarity_threshold": 0.4,
  "auto_equip": [
    "n8n.slack_message"
  ],
  "excluded": [
    "n8n.research_dataset"
  ],
  "filters": {
    "tags": ["development", "deployment", "communication", "ci-cd"],
    "priority_max": 5
  }
}
```

**Characteristics**:
- Standard recall interval (5)
- Conservative instrument count (2) to keep prompts focused
- Always includes Slack for team communication
- Broader priority range for specialized tools

### Communication Profile

Specialized for messaging and notifications.

```json
{
  "enabled": true,
  "recall_interval": 7,
  "max_instruments": 4,
  "similarity_threshold": 0.3,
  "auto_equip": [
    "n8n.slack_message",
    "n8n.email_workflow",
    "n8n.teams_notification"
  ],
  "excluded": [],
  "filters": {
    "tags": ["communication", "messaging", "notification"],
    "priority_max": 4
  }
}
```

**Characteristics**:
- Less frequent recall (stable workflow)
- More instruments (4) for coverage
- Multiple auto-equipped communication tools
- Focused on communication tags only

### Minimal Profile

Minimal configuration relying on global settings.

```json
{
  "enabled": true
}
```

**Characteristics**:
- Uses all global defaults
- No profile-specific overrides
- Good starting point for new profiles

## Configuration Workflow

### Initial Setup

1. **Deploy Extension**:
   ```bash
   python -m python.helpers.deploy_instrument_recall --profiles myprofile
   ```

2. **Start with Defaults**: Use generated `instruments.json` as-is initially

3. **Test and Observe**: Use the profile and monitor:
   - Which instruments are recalled
   - How often recall happens
   - Relevance of recalled instruments

4. **Iterate**: Adjust configuration based on observations

### Optimization Process

1. **Tune Threshold**:
   - Too many irrelevant instruments? Increase `similarity_threshold`
   - Missing relevant instruments? Decrease `similarity_threshold`

2. **Adjust Count**:
   - Prompts too large? Decrease `max_instruments`
   - Not enough options? Increase `max_instruments`

3. **Add Auto-Equip**:
   - Identify frequently-used instruments
   - Add to `auto_equip` list

4. **Filter by Tags**:
   - Review instrument tags in metadata
   - Add relevant tags to `filters.tags`

5. **Exclude Unwanted**:
   - Note instruments that appear but aren't useful
   - Add to `excluded` list

### Validation

After making changes, validate the configuration:

```bash
python -m python.helpers.deploy_instrument_recall --profiles myprofile --validate
```

## Best Practices

### 1. Start Simple
Begin with minimal configuration and add complexity only as needed.

```json
{
  "enabled": true,
  "max_instruments": 2,
  "similarity_threshold": 0.4
}
```

### 2. Document Your Choices
Add comments (if using JSON5 or JSONC) or keep separate documentation:

```json
{
  "enabled": true,
  "recall_interval": 3,
  "max_instruments": 3,
  "auto_equip": [
    "n8n.slack_message"
  ]
}
```

Separate notes: "Slack auto-equipped because we use it for all critical notifications"

### 3. Test Changes Incrementally
Change one parameter at a time and observe effects before making more changes.

### 4. Profile-Specific Tags
Create custom tags in instrument metadata that align with profile purposes:

```json
{
  "filters": {
    "tags": ["researcher-essential", "data-science"]
  }
}
```

### 5. Monitor Prompt Size
Keep track of how many tokens instruments add to prompts:
- Check agent logs for prompt sizes
- Balance coverage vs. efficiency

### 6. Use Priority Tiers
Establish clear priority guidelines in your team:
- Priority 1: Essential tools
- Priority 2: Very useful tools
- Priority 3: Task-specific tools
- Priority 4+: Specialized/experimental

### 7. Review Periodically
Instrument needs change over time:
- Monthly: Review auto_equip and excluded lists
- Quarterly: Reassess thresholds and filters
- After new instruments: Update relevant profiles

## Troubleshooting

### No Instruments Recalled

**Check**:
1. Profile has extension deployed
2. `enabled: true` in config
3. Instruments exist for this profile in metadata
4. Threshold not too high
5. Tag filters not too restrictive

**Solution**:
```json
{
  "enabled": true,
  "similarity_threshold": 0.3,  // Lower threshold
  "filters": {}  // Remove restrictive filters temporarily
}
```

### Too Many Irrelevant Instruments

**Check**:
1. Threshold may be too low
2. No tag filtering applied
3. Priority filter too permissive

**Solution**:
```json
{
  "similarity_threshold": 0.45,  // Raise threshold
  "max_instruments": 2,          // Reduce count
  "filters": {
    "tags": ["relevant", "tags"],
    "priority_max": 3            // Only high-priority
  }
}
```

### Critical Instrument Not Recalled

**Solution**: Use auto-equip
```json
{
  "auto_equip": ["n8n.critical_tool"]
}
```

### Performance Issues

**Check**:
1. Recall interval may be too low
2. Max instruments too high

**Solution**:
```json
{
  "recall_interval": 10,  // Less frequent
  "max_instruments": 2    // Fewer instruments
}
```

## Migration Guide

### From Manual Instrument Loading

**Before** (manual):
- Load instruments via knowledge tool
- Manual selection each time

**After** (automatic):
```json
{
  "enabled": true,
  "auto_equip": ["your.frequently.used.instrument"],
  "filters": {
    "tags": ["your", "common", "tasks"]
  }
}
```

### From Global Settings Only

**Before** (global only):
```python
"instrument_recall_enabled": True
"instrument_recall_interval": 5
```

**After** (profile-specific):
```json
{
  "recall_interval": 3,  // Override for this profile
  "filters": {           // Add profile-specific filtering
    "tags": ["profile-specific-tag"]
  }
}
```

## See Also

- [Instrument Recall Extension](../extensions/instrument-recall.md)
- [Instrument Metadata System](../instrument-metadata.md)
- [Agent Profiles](../profiles.md)
- [Extension System](../extensibility.md)


