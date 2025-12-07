from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files, memory
import json
import os
from pathlib import Path


class RegisterInstrument(ApiHandler):
    """API endpoint for registering n8n workflows as instruments."""
    
    @classmethod
    def requires_auth(cls) -> bool:
        return False  # No web auth required
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # No CSRF required
    
    @classmethod
    def requires_api_key(cls) -> bool:
        return True  # Require API key
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Register a new n8n workflow as an instrument.
        
        Expected input:
        {
            "workflow_name": "email_workflow",
            "webhook_url": "https://n8n.com/webhook/abc123",
            "description": "Send automated emails",
            "parameters": ["recipient", "template", "data"],
            "profiles": ["default"],  # optional
            "tags": [],  # optional
            "priority": 5,  # optional
            "display_name": "",  # optional
            "category": ""  # optional
        }
        """
        # Extract parameters
        workflow_name = input.get("workflow_name", "").strip()
        webhook_url = input.get("webhook_url", "").strip()
        description = input.get("description", "").strip()
        parameters = input.get("parameters", [])
        
        # Extract metadata parameters (with defaults)
        profiles = input.get("profiles", ["default"])
        if isinstance(profiles, str):
            profiles = [p.strip() for p in profiles.split(",") if p.strip()]
        tags = input.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        priority = input.get("priority", 5)
        display_name = input.get("display_name", "").strip() or description
        category = input.get("category", "").strip() or "N8N Workflow"
        
        # Validate inputs
        if not workflow_name:
            return Response('{"error": "workflow_name is required"}', status=400, mimetype="application/json")
        
        if not webhook_url:
            return Response('{"error": "webhook_url is required"}', status=400, mimetype="application/json")
        
        if not description:
            return Response('{"error": "description is required"}', status=400, mimetype="application/json")
        
        # Validate workflow name format (lowercase with underscores only)
        if not workflow_name.replace("_", "").isalnum():
            return Response(
                '{"error": "workflow_name must contain only lowercase letters, numbers, and underscores"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            # Setup paths
            n8n_base_path = files.get_abs_path("instruments/custom/n8n")
            config_path = Path(n8n_base_path) / "config.json"
            workflows_dir = Path(n8n_base_path) / "workflows"
            
            # Ensure directories exist
            os.makedirs(n8n_base_path, exist_ok=True)
            os.makedirs(workflows_dir, exist_ok=True)
            
            # Load existing config
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {
                    "n8n_base_url": "https://your-n8n-instance.com",
                    "workflows": {}
                }
            
            # Parse webhook URL
            if webhook_url.startswith("http"):
                # Full URL provided - extract base and path
                if "/webhook/" in webhook_url:
                    idx = webhook_url.find("/webhook/")
                    base_url = webhook_url[:idx]
                    webhook_path = webhook_url[idx:]
                    config["n8n_base_url"] = base_url
                elif "/webhook-test/" in webhook_url:
                    # Handle test webhooks
                    idx = webhook_url.find("/webhook-test/")
                    base_url = webhook_url[:idx]
                    webhook_path = webhook_url[idx:]
                    config["n8n_base_url"] = base_url
                else:
                    return Response(
                        '{"error": "Webhook URL must contain \'/webhook/\' or \'/webhook-test/\' path"}',
                        status=400,
                        mimetype="application/json"
                    )
            else:
                # Just path provided - use existing base URL
                webhook_path = webhook_url if webhook_url.startswith("/") else f"/{webhook_url}"
            
            # Add workflow to config
            config["workflows"][workflow_name] = {
                "webhook_path": webhook_path,
                "description": description,
                "parameters": parameters if isinstance(parameters, list) else []
            }
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Create instrument description
            param_docs = "\n".join([f"- `{param}`: Parameter for {param}" for param in parameters]) if parameters else "No parameters required"
            
            example_params = ""
            if parameters:
                example_params = " \\\n  " + " \\\n  ".join([f'--{param} "value"' for param in parameters[:3]])
            
            description_content = f"""# Problem
{description}

# Solution
Execute the n8n workflow via bridge:

```bash
python /a0/instruments/custom/n8n/bridge.py {workflow_name}{example_params}
```

## Parameters
{param_docs}

## Expected Output
- Success: "✓ {description}: [Result details]"
- Error: "✗ {description} Error: [Error message]"

## Notes
- Configure this workflow in your n8n instance first
- Update the webhook URL in config.json if needed
- Test with: python /a0/instruments/custom/n8n/test_workflow.py {workflow_name}
"""
            
            # Save instrument description
            description_path = workflows_dir / f"{workflow_name}.md"
            with open(description_path, 'w') as f:
                f.write(description_content)
            
            # Register metadata in central registry
            from python.helpers.instrument_metadata import InstrumentMetadata
            
            instrument_id = f"n8n.{workflow_name}"
            InstrumentMetadata.set_instrument_metadata(
                instrument_id=instrument_id,
                metadata={
                    "type": "n8n",
                    "source_path": f"instruments/custom/n8n/workflows/{workflow_name}.md",
                    "profiles": profiles,
                    "tags": tags,
                    "priority": priority,
                    "enabled": True,
                    "metadata": {
                        "display_name": display_name,
                        "category": category
                    }
                }
            )
            
            # Get context for memory reload
            ctxid = input.get("context_id", "")
            if ctxid:
                context = self.use_context(ctxid)
                # Reload memory to embed new instrument
                await memory.Memory.reload(context.agent0)
                context.log.set_initial_progress()
            
            return {
                "success": True,
                "message": f"Workflow '{workflow_name}' registered successfully",
                "workflow_id": workflow_name,
                "config_path": str(config_path),
                "description_path": str(description_path),
                "next_steps": [
                    "Review the generated instrument description",
                    f"Test with: python test_workflow.py {workflow_name}",
                    "Restart Agent Zero if memory wasn't reloaded"
                ]
            }
            
        except json.JSONDecodeError as e:
            return Response(
                f'{{"error": "Invalid JSON in config file: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )
        except Exception as e:
            return Response(
                f'{{"error": "Failed to register workflow: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )

