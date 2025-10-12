#!/bin/bash
# Register Slack Message Workflow with Agent Zero
# Replace YOUR_API_TOKEN with your actual token from Settings > MCP > A0 MCP Server > MCP Server Token

curl -X POST http://localhost:50080/register_instrument \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: YOUR_API_TOKEN" \
  -d '{
    "workflow_name": "slack_message",
    "webhook_url": "https://silveraiautomation.app.n8n.cloud/webhook-test/2cbfd243-09ea-4f58-96e4-e66f82b8ef45",
    "description": "Send Slack Message to a specific channel",
    "parameters": ["Message"]
  }'

