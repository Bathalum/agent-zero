# Problem
Send Slack Message to a specific channel

# Solution
Execute the n8n workflow via bridge:

```bash
python /a0/instruments/custom/n8n/bridge.py slack_message \
  --Message "value"
```

## Parameters
- `Message`: [Description needed]

## Expected Output
- Success: "✓ Send Slack Message to a specific channel: [Result details]"
- Error: "✗ Send Slack Message to a specific channel Error: [Error message]"


## Notes
- Configure this workflow in your n8n instance first
- Update the webhook URL in config.json
- Test with the test_workflow.py script before use
