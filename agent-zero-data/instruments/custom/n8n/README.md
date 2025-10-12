# N8N Workflow Integration

This directory contains the bridge system for integrating n8n workflows with Agent Zero as "skills".

## Quick Start

### 1. Configure Your N8N Instance

Edit `config.json` and set your n8n base URL:

```json
{
  "n8n_base_url": "https://your-n8n-instance.com",
  "workflows": {}
}
```

### 2. Register a Workflow

Use the registration helper:

```bash
python register_workflow.py \
  --name email_workflow \
  --webhook https://your-n8n-instance.com/webhook/abc123 \
  --description "Send automated emails" \
  --params recipient,template,data
```

Or use the API endpoint:

```bash
curl -X POST http://localhost:50001/register_instrument \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "email_workflow",
    "webhook_url": "https://your-n8n-instance.com/webhook/abc123",
    "description": "Send automated emails",
    "parameters": ["recipient", "template", "data"]
  }'
```

### 3. Test the Workflow

```bash
python test_workflow.py email_workflow --recipient "test@example.com"
```

### 4. Restart Agent Zero

Restart Agent Zero to embed the new instrument into memory.

### 5. Use with Agent

Ask Agent Zero to use your workflow:

```
User: "Can you send a welcome email to test@example.com?"
```

Agent Zero will:
1. Search memory for email-related instruments
2. Find your workflow description
3. Execute it using the bridge
4. Return the result

## Files

- **bridge.py** - Main execution bridge for n8n webhooks
- **config.json** - Workflow registry and n8n configuration
- **register_workflow.py** - CLI helper for registering workflows
- **test_workflow.py** - Testing utility
- **workflows/** - Instrument descriptions (one .md file per workflow)

## How It Works

### Instrument Pattern

Each workflow is registered as an "instrument" - a skill that Agent Zero can discover and use:

1. **Discovery**: Instrument descriptions are embedded in Agent Zero's memory
2. **Search**: When needed, agent searches memory for relevant instruments
3. **Execution**: Agent uses code_execution tool to run the bridge script
4. **Response**: Bridge provides clean output that agent interprets

### Bridge Architecture

The bridge script:
- Loads workflow configuration from `config.json`
- Makes HTTP POST requests to n8n webhooks
- Handles errors with retry logic
- Formats output for Agent Zero consumption

### Output Format

Success:
```
✓ [Workflow Name]: [Result summary]
```

Error:
```
✗ [Workflow Name] Error: [Clean error message]
```

## Advanced Usage

### Manual Registration

Edit `config.json` directly:

```json
{
  "n8n_base_url": "https://your-n8n-instance.com",
  "workflows": {
    "custom_workflow": {
      "webhook_path": "/webhook/xyz789",
      "description": "Custom workflow description",
      "parameters": ["param1", "param2"]
    }
  }
}
```

Create instrument description in `workflows/custom_workflow.md` following the pattern in existing examples.

### Listing Workflows

Via API:
```bash
curl http://localhost:50001/list_instruments
```

Via CLI:
```bash
python -c "import json; print(json.dumps(json.load(open('config.json'))['workflows'], indent=2))"
```

### Testing Connectivity Only

```bash
python test_workflow.py email_workflow --connectivity-only
```

### Validating Configuration

```bash
python test_workflow.py email_workflow --validate-only
```

## Troubleshooting

### Workflow Not Found

- Check that workflow exists in `config.json`
- Verify instrument description exists in `workflows/` directory
- Restart Agent Zero to embed new instruments

### Connection Errors

- Verify n8n_base_url is correct
- Check webhook_path is valid
- Test webhook accessibility: `curl -X POST https://your-n8n-instance.com/webhook/abc123 -d '{"test":true}'`

### Agent Doesn't Find Workflow

- Check instrument description is clear and descriptive
- Verify memory embedding completed (check memory dashboard)
- Try more specific problem description in .md file

### Execution Fails

- Run test_workflow.py to diagnose
- Check n8n workflow is active
- Verify parameters match workflow expectations
- Review n8n workflow execution logs

## Token Efficiency

This system keeps token costs minimal:

- **System Prompt**: No workflow definitions (zero tokens)
- **Discovery**: Only search query (~100 tokens)
- **Retrieval**: Only relevant workflow description (~200 tokens)
- **Execution**: Only command and output (~100 tokens)

**Total per workflow use: ~400 tokens vs. 10,000+ with traditional approaches**

## Extension

### Support Other Platforms

The bridge pattern works for any webhook-based automation:

- Make.com
- Zapier
- Custom APIs
- Workflow orchestrators

Just adapt the bridge script or create variants.

### Dynamic UI Integration

Bridge can return structured metadata for rich frontend rendering:

```python
# In bridge.py, format output as:
output = {
    "status": "success",
    "result_type": "email_sent",
    "display_data": {
        "to": "user@example.com",
        "subject": "Welcome"
    }
}
print(json.dumps(output))
```

Frontend interprets `result_type` to render appropriate UI component.

## Contributing

When adding new workflows:

1. Use descriptive workflow IDs (lowercase_with_underscores)
2. Document all parameters clearly
3. Include examples in instrument descriptions
4. Test thoroughly before committing
5. Update this README if adding new features

## Support

- Issues: Check test_workflow.py output for diagnostics
- Documentation: See Agent Zero docs on instruments
- Examples: Review existing workflows in workflows/ directory

