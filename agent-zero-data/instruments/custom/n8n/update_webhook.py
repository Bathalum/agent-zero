#!/usr/bin/env python3
"""
Helper script to update n8n webhook URL in config.json
"""

import json
import sys
from pathlib import Path

def update_webhook(workflow_id: str, webhook_url: str):
    """Update webhook URL for a workflow in config.json"""
    config_path = Path(__file__).parent / "config.json"
    
    # Load config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return False
    
    # Check workflow exists
    if workflow_id not in config.get("workflows", {}):
        print(f"✗ Workflow '{workflow_id}' not found in config")
        print(f"Available workflows: {', '.join(config.get('workflows', {}).keys())}")
        return False
    
    # Parse webhook URL
    if webhook_url.startswith("http"):
        # Full URL provided - extract base and path
        if "/webhook" in webhook_url:
            idx = webhook_url.find("/webhook")
            base_url = webhook_url[:idx]
            webhook_path = webhook_url[idx:]
            config["n8n_base_url"] = base_url
            config["workflows"][workflow_id]["webhook_path"] = webhook_path
        else:
            print("✗ Error: Webhook URL must contain '/webhook' path")
            return False
    else:
        # Just path provided
        webhook_path = webhook_url if webhook_url.startswith("/") else f"/{webhook_url}"
        config["workflows"][workflow_id]["webhook_path"] = webhook_path
    
    # Save config
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Updated webhook for '{workflow_id}'")
        print(f"  Base URL: {config.get('n8n_base_url')}")
        print(f"  Webhook Path: {config['workflows'][workflow_id]['webhook_path']}")
        return True
    except Exception as e:
        print(f"✗ Error saving config: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python update_webhook.py <workflow_id> <webhook_url>")
        print("\nExamples:")
        print('  python update_webhook.py slack_message "https://your-n8n.app.n8n.cloud/webhook/abc123"')
        print('  python update_webhook.py slack_message "/webhook/abc123"  # Uses existing base URL')
        print("\nTo get your webhook URL from n8n:")
        print("1. Open your n8n workflow")
        print("2. Click on the Webhook node")
        print("3. Copy the 'Production URL' or 'Test URL'")
        print("4. Use that URL with this script")
        sys.exit(1)
    
    workflow_id = sys.argv[1]
    webhook_url = sys.argv[2]
    
    if update_webhook(workflow_id, webhook_url):
        print("\n✓ Configuration updated successfully!")
        print("You can now test the workflow with:")
        print(f'  python3 /a0/instruments/custom/n8n/bridge.py {workflow_id} --Message "test"')
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

