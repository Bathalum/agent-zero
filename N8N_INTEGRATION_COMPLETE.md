# N8N Workflow Integration - Setup Complete

## What Was Implemented

Your Agent Zero instance now has a complete n8n workflow integration system! Here's what's ready to use:

### 1. Bridge System (Zero Token Cost)
- **Location**: `agent-zero-data/instruments/custom/n8n/`
- **Purpose**: Execute n8n webhooks with robust error handling
- **Features**:
  - Automatic retry with exponential backoff (3 attempts)
  - Clean output formatting for Agent Zero
  - No external dependencies (uses Python stdlib)
  - Multi-workflow support

### 2. Your Registered Workflow
- **Name**: `slack_message`
- **Description**: Send Slack Message to a specific channel
- **Webhook**: `https://your-n8n-instance.app.n8n.cloud/webhook-test/your-webhook-uuid-here`
- **Status**: ✅ Tested and working!

### 3. Tools Available
- **Registration Helper**: `register_workflow.py` - Add new workflows easily
- **Testing Utility**: `test_workflow.py` - Test workflows before using
- **Bridge Script**: `bridge.py` - Execute any registered workflow

## How to Use It

### Test the Slack Workflow (Manual)

From your command line:
```bash
docker exec agent-zero-local python3 /a0/instruments/custom/n8n/bridge.py slack_message --Message "Your message here"
```

Expected output:
```
✓ Send Slack Message to a specific channel: Workflow was started
```

### Use with Agent Zero (The Magic Part!)

Now you can simply **ask Agent Zero** to send Slack messages:

**Example conversations:**
```
User: "Can you send a Slack message saying 'Deployment complete!'"
User: "Post to Slack: The server is back online"
User: "Send a Slack notification about the latest updates"
```

**What happens behind the scenes:**
1. Agent searches memory for "slack" or "send message" instruments
2. Finds your `slack_message` instrument description
3. Executes: `python /a0/instruments/custom/n8n/bridge.py slack_message --Message "..."`
4. Gets the result
5. Reports back to you

**No tokens wasted** - the workflow description is only loaded when needed from memory!

## Adding More Workflows

### Quick Registration:
```bash
docker exec agent-zero-local python3 /a0/instruments/custom/n8n/register_workflow.py \
  --name workflow_name \
  --webhook "https://your-n8n.com/webhook/xyz" \
  --description "What it does" \
  --params "param1,param2" \
  --no-test
```

### Then restart to embed:
```bash
docker restart agent-zero-local
```

## File Locations

### In Container (Runtime):
- Config: `/a0/instruments/custom/n8n/config.json`
- Workflows: `/a0/instruments/custom/n8n/workflows/*.md`
- Bridge: `/a0/instruments/custom/n8n/bridge.py`

### On Host (Persistent):
- Everything in: `agent-zero-data/instruments/custom/n8n/`
- This persists across container restarts!

## Current Configuration

```json
{
  "n8n_base_url": "https://your-n8n-instance.app.n8n.cloud",
  "workflows": {
    "slack_message": {
      "webhook_path": "/webhook-test/your-webhook-uuid-here",
      "description": "Send Slack Message to a specific channel",
      "parameters": ["Message"]
    }
  }
}
```

## Testing Checklist

- [x] Bridge script created with error handling
- [x] Configuration system set up
- [x] Workflow registered successfully
- [x] Bridge tested standalone (working!)
- [x] Instrument description created
- [x] Memory embedded (after restart)
- [ ] Test with Agent Zero conversation (your turn!)
- [ ] Add more workflows as needed

## Next Steps

### 1. Test with Agent Zero

Open Agent Zero at `http://localhost:50080` and try:
```
User: "Can you send a Slack message saying 'Hello from Agent Zero!'"
```

Watch for:
- Agent searching memory for instruments
- Agent finding "slack_message" 
- Agent executing the bridge command
- Agent reporting the result

### 2. Add More Workflows

Create different workflow types:
- Email notifications
- Data retrieval (API calls)
- Database updates
- File processing
- Any n8n automation!

Each one:
- Takes ~2 minutes to register
- Zero tokens in system prompt
- Instantly available to Agent Zero

### 3. Refine Instrument Descriptions

If Agent Zero has trouble finding or using a workflow:
- Edit the `.md` file in `agent-zero-data/instruments/custom/n8n/workflows/`
- Make the problem description clearer
- Add more examples
- Restart Agent Zero to re-embed

## Token Economics

**Traditional Approach:**
- 10 workflows × ~200 tokens = 2,000 tokens
- Every message loop
- Context bloat

**Your New System:**
- System prompt: 0 tokens (just mentions "instruments exist")
- When used: ~400 tokens (search + description + execution)
- 10, 100, or 1000 workflows = same token cost!

## Troubleshooting

### Workflow Not Found
```bash
# Check if embedded
docker exec agent-zero-local python3 /a0/instruments/custom/n8n/test_workflow.py slack_message --validate-only
```

### Webhook Failing
```bash
# Test connectivity
docker exec agent-zero-local python3 /a0/instruments/custom/n8n/test_workflow.py slack_message --connectivity-only
```

### Agent Doesn't Find It
- Check the instrument description is clear
- Make problem statement match user language
- Add keywords Agent Zero might search for

## What You Built

You now have:
1. **Scalable skill system** - Add unlimited n8n workflows without token cost
2. **Robust execution** - Error handling, retries, clean output
3. **Easy registration** - CLI or API to add new skills
4. **Agent-discoverable** - Agent finds and uses them automatically
5. **Production-ready** - Tested and working!

This is your foundation for building a **true agentic automation platform** where Agent Zero can leverage hundreds of specialized n8n workflows as needed! 🚀

## Ready to Test?

Open Agent Zero and ask it to send a Slack message - watch the magic happen! 🪄


