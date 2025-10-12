from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files
import json
import os
from pathlib import Path


class ListInstruments(ApiHandler):
    """API endpoint for listing registered n8n workflows."""
    
    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        List all registered n8n workflows.
        
        Returns:
        {
            "instruments": [
                {
                    "workflow_id": "email_workflow",
                    "description": "Send automated emails",
                    "parameters": ["recipient", "template", "data"],
                    "webhook_path": "/webhook/abc123"
                }
            ]
        }
        """
        try:
            # Setup paths
            n8n_base_path = files.get_abs_path("instruments/custom/n8n")
            config_path = Path(n8n_base_path) / "config.json"
            workflows_dir = Path(n8n_base_path) / "workflows"
            
            # Check if config exists
            if not config_path.exists():
                return {
                    "instruments": [],
                    "message": "No n8n workflows registered yet"
                }
            
            # Load config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Build instrument list
            instruments = []
            workflows = config.get("workflows", {})
            
            for workflow_id, workflow_config in workflows.items():
                # Check if instrument description exists
                description_path = workflows_dir / f"{workflow_id}.md"
                has_description = description_path.exists()
                
                instrument_info = {
                    "workflow_id": workflow_id,
                    "description": workflow_config.get("description", ""),
                    "parameters": workflow_config.get("parameters", []),
                    "webhook_path": workflow_config.get("webhook_path", ""),
                    "has_description": has_description,
                    "description_path": str(description_path) if has_description else None
                }
                
                instruments.append(instrument_info)
            
            # Sort by workflow_id
            instruments.sort(key=lambda x: x["workflow_id"])
            
            return {
                "instruments": instruments,
                "count": len(instruments),
                "n8n_base_url": config.get("n8n_base_url", "")
            }
            
        except json.JSONDecodeError as e:
            return Response(
                f'{{"error": "Invalid JSON in config file: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )
        except Exception as e:
            return Response(
                f'{{"error": "Failed to list instruments: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )

