# Setting Up N8N Webhook URLs

## Quick Fix for "Webhook not found (404)" Error

The error you're seeing means the webhook URL in `config.json` is still set to placeholder values. Here's how to fix it:

## Step 1: Get Your Webhook URL from n8n

1. **Open your n8n instance** in a browser
2. **Open the workflow** that sends Slack messages
3. **Click on the Webhook node** (the trigger node)
4. **Copy the webhook URL**. You'll see either:
   - **Production URL**: `https://your-instance.app.n8n.cloud/webhook/abc123...`
   - **Test URL**: `https://your-instance.app.n8n.cloud/webhook-test/abc123...`
5. **Make sure the workflow is activated** (toggle switch in top-right)

## Step 2: Update the Config

### Option A: Using the Helper Script (Recommended)

```bash
python3 /a0/instruments/custom/n8n/update_webhook.py slack_message "https://your-instance.app.n8n.cloud/webhook/your-uuid-here"
```

### Option B: Using the API

```bash
curl -X POST http://localhost:50080/register_instrument \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: YOUR_API_TOKEN" \
  -d '{
    "workflow_name": "slack_message",
    "webhook_url": "https://your-instance.app.n8n.cloud/webhook/your-uuid-here",
    "description": "Send Slack Message to a specific channel",
    "parameters": ["Message"]
  }'
```

### Option C: Manual Edit

Edit `/a0/instruments/custom/n8n/config.json`:

```json
{
  "n8n_base_url": "https://your-instance.app.n8n.cloud",
  "workflows": {
    "slack_message": {
      "webhook_path": "/webhook/your-actual-uuid-here",
      "description": "Send Slack Message to a specific channel",
      "parameters": ["Message"]
    }
  }
}
```

## Step 3: Test the Webhook

```bash
python3 /a0/instruments/custom/n8n/bridge.py slack_message --Message "Test message"
```

You should see:
```
✓ Send Slack Message to a specific channel: [success message]
```

## Common Issues

### "Webhook not found (404)"

- **Check the URL is correct**: Copy it exactly from n8n
- **Check the workflow is activated**: Toggle must be ON in n8n
- **Check you're using the right URL**: Production vs Test URL
- **Verify the webhook path**: Should start with `/webhook/` or `/webhook-test/`

### "Connection failed"

- **Check n8n is accessible**: Can you reach it in a browser?
- **Check network**: Is the container able to reach the internet?
- **Check firewall**: Is port 443 (HTTPS) open?

### "Server error (500)"

- **Check n8n workflow logs**: Look for errors in the workflow execution
- **Check workflow configuration**: Make sure all nodes are properly configured
- **Test in n8n UI**: Try executing the workflow manually in n8n

## Finding Your Webhook URL

The webhook URL format depends on your n8n setup:

- **n8n Cloud**: `https://your-instance.app.n8n.cloud/webhook/abc123...`
- **Self-hosted**: `https://your-domain.com/webhook/abc123...`
- **Local development**: `http://localhost:5678/webhook/abc123...`

The webhook node in n8n will show you the exact URL to use.

## Next Steps

After updating the webhook URL:

1. **Test it works**: Run the bridge script manually
2. **Restart Agent Zero** (if needed): Some changes require a restart
3. **Try using the skill**: Ask the agent to send a Slack message

## Need Help?

- Check the n8n workflow execution logs
- Test the webhook directly with curl:
  ```bash
  curl -X POST https://your-instance.app.n8n.cloud/webhook/your-uuid \
    -H "Content-Type: application/json" \
    -d '{"Message": "test"}'
  ```
- Review the bridge.py error messages for more details

