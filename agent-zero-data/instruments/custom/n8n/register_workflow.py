#!/usr/bin/env python3
"""
N8N Workflow Registration Helper
Automates the process of registering new n8n workflows as Agent Zero instruments.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Optional
import os
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class WorkflowRegistrar:
    """Helper for registering n8n workflows as instruments."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize registrar with base path."""
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = base_path
        self.config_path = base_path / "config.json"
        self.workflows_dir = base_path / "workflows"
        
    def load_config(self) -> dict:
        """Load existing configuration."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "n8n_base_url": "https://your-n8n-instance.com",
            "workflows": {}
        }
    
    def save_config(self, config: dict) -> None:
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def test_webhook(self, webhook_url: str) -> tuple[bool, str]:
        """Test if webhook is reachable using urllib."""
        try:
            json_data = json.dumps({"test": True}).encode('utf-8')
            req = Request(
                webhook_url,
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urlopen(req, timeout=10) as response:
                status_code = response.getcode()
                # Any 2xx response is considered reachable
                return True, f"Webhook is reachable (HTTP {status_code})"
                
        except HTTPError as e:
            if e.code == 404:
                return False, "Webhook not found (404)"
            elif e.code >= 500:
                return False, f"Server error ({e.code})"
            # Any 4xx (except 404) is still "reachable"
            return True, f"Webhook is reachable (HTTP {e.code})"
            
        except URLError as e:
            if "timeout" in str(e).lower():
                return False, "Connection timeout"
            return False, f"Connection failed - check URL and network: {str(e.reason)[:50]}"
            
        except Exception as e:
            return False, f"Test failed: {str(e)[:100]}"
    
    def create_instrument_description(
        self,
        workflow_id: str,
        description: str,
        parameters: List[str],
        examples: Optional[List[str]] = None
    ) -> str:
        """Generate instrument description markdown."""
        # Build parameter documentation
        param_docs = "\n".join([f"- `{param}`: [Description needed]" for param in parameters])
        
        # Build example command
        example_params = " \\\n  ".join([f'--{param} "value"' for param in parameters])
        example_cmd = f"python /a0/instruments/custom/n8n/bridge.py {workflow_id}"
        if example_params:
            example_cmd += f" \\\n  {example_params}"
        
        # Additional examples
        examples_section = ""
        if examples:
            examples_section = "\n\n## Examples\n" + "\n".join([f"```bash\n{ex}\n```" for ex in examples])
        
        return f"""# Problem
{description}

# Solution
Execute the n8n workflow via bridge:

```bash
{example_cmd}
```

## Parameters
{param_docs if param_docs else "No parameters required"}

## Expected Output
- Success: "✓ {description}: [Result details]"
- Error: "✗ {description} Error: [Error message]"
{examples_section}

## Notes
- Configure this workflow in your n8n instance first
- Update the webhook URL in config.json
- Test with the test_workflow.py script before use
"""
    
    def register_workflow(
        self,
        workflow_id: str,
        webhook_url: str,
        description: str,
        parameters: List[str],
        test_webhook: bool = True,
        examples: Optional[List[str]] = None
    ) -> bool:
        """
        Register a new workflow.
        Returns True on success, False on failure.
        """
        print(f"Registering workflow: {workflow_id}")
        
        # Parse webhook URL
        if webhook_url.startswith("http"):
            # Full URL provided - extract base and path
            if "/webhook" in webhook_url:
                # Find the webhook part in the URL
                idx = webhook_url.find("/webhook")
                base_url = webhook_url[:idx]
                webhook_path = webhook_url[idx:]
            else:
                print("Error: Invalid webhook URL format. Should contain '/webhook' path")
                return False
        else:
            # Relative path provided
            base_url = None
            webhook_path = webhook_url if webhook_url.startswith("/") else f"/{webhook_url}"
        
        # Test webhook if requested
        if test_webhook:
            print("Testing webhook connectivity...")
            if base_url:
                test_url = webhook_url
            else:
                config = self.load_config()
                test_url = config.get("n8n_base_url", "").rstrip("/") + webhook_path
            
            success, message = self.test_webhook(test_url)
            print(f"  {message}")
            if not success:
                response = input("Webhook test failed. Continue anyway? (y/N): ")
                if response.lower() != "y":
                    return False
        
        # Load config
        config = self.load_config()
        
        # Update base URL if provided
        if base_url:
            config["n8n_base_url"] = base_url
        
        # Add workflow
        config["workflows"][workflow_id] = {
            "webhook_path": webhook_path,
            "description": description,
            "parameters": parameters
        }
        
        # Save config
        print("Updating config.json...")
        self.save_config(config)
        
        # Create workflows directory if needed
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # Create instrument description
        print(f"Creating instrument description...")
        description_path = self.workflows_dir / f"{workflow_id}.md"
        description_content = self.create_instrument_description(
            workflow_id, description, parameters, examples
        )
        
        with open(description_path, 'w') as f:
            f.write(description_content)
        
        print(f"✓ Workflow registered successfully!")
        print(f"  Config: {self.config_path}")
        print(f"  Description: {description_path}")
        print("\nNext steps:")
        print("1. Review and edit the instrument description if needed")
        print("2. Test with: python test_workflow.py " + workflow_id)
        print("3. Restart Agent Zero to embed the new instrument")
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Register n8n workflows as Agent Zero instruments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register with full webhook URL
  python register_workflow.py \\
    --name email_workflow \\
    --webhook https://n8n.example.com/webhook/abc123 \\
    --description "Send automated emails" \\
    --params recipient,template,data

  # Register with relative webhook path
  python register_workflow.py \\
    --name notification_workflow \\
    --webhook /webhook/xyz789 \\
    --description "Send notifications" \\
    --params message,channel
        """
    )
    
    parser.add_argument(
        "--name",
        required=True,
        help="Workflow ID (use lowercase with underscores)"
    )
    
    parser.add_argument(
        "--webhook",
        required=True,
        help="Webhook URL or path"
    )
    
    parser.add_argument(
        "--description",
        required=True,
        help="Human-readable description of what the workflow does"
    )
    
    parser.add_argument(
        "--params",
        help="Comma-separated list of parameter names",
        default=""
    )
    
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip webhook connectivity test"
    )
    
    parser.add_argument(
        "--example",
        action="append",
        help="Add example command (can be used multiple times)"
    )
    
    args = parser.parse_args()
    
    # Parse parameters
    parameters = [p.strip() for p in args.params.split(",") if p.strip()]
    
    # Initialize registrar
    registrar = WorkflowRegistrar()
    
    # Register workflow
    try:
        success = registrar.register_workflow(
            workflow_id=args.name,
            webhook_url=args.webhook,
            description=args.description,
            parameters=parameters,
            test_webhook=not args.no_test,
            examples=args.example
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

