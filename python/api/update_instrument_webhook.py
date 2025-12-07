from python.helpers.api import ApiHandler, Request, Response
from python.helpers.instrument_metadata import InstrumentMetadata
from python.helpers import files
import json
import os
from pathlib import Path


class UpdateInstrumentWebhook(ApiHandler):
    """API endpoint for updating webhook URLs for n8n instruments."""
    
    @classmethod
    def requires_auth(cls) -> bool:
        return False  # No web auth required
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # No CSRF required
    
    @classmethod
    def requires_api_key(cls) -> bool:
        return True  # Require API key for updates
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Update webhook URL for an n8n instrument.
        
        Parameters:
        - instrument_id: str (required) - Instrument ID (e.g., "n8n.slack_message")
        - webhook_url: str (required) - Full webhook URL or just the path
        """
        # Extract and validate instrument_id
        instrument_id = input.get("instrument_id", "").strip()
        webhook_url = input.get("webhook_url", "").strip()
        
        if not instrument_id:
            return Response(
                '{"error": "instrument_id is required"}',
                status=400,
                mimetype="application/json"
            )
        
        if not webhook_url:
            return Response(
                '{"error": "webhook_url is required"}',
                status=400,
                mimetype="application/json"
            )
        
        # Check if instrument exists and is n8n type
        existing = InstrumentMetadata.get_instrument_metadata(instrument_id)
        if not existing:
            return Response(
                f'{{"error": "Instrument \'{instrument_id}\' not found"}}',
                status=404,
                mimetype="application/json"
            )
        
        if existing.get("type") != "n8n":
            return Response(
                f'{{"error": "Instrument \'{instrument_id}\' is not an n8n workflow. Webhook URLs can only be updated for n8n instruments."}}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            # Extract workflow name from instrument_id (e.g., "n8n.slack_message" -> "slack_message")
            if not instrument_id.startswith("n8n."):
                return Response(
                    f'{{"error": "Invalid instrument_id format for n8n workflow. Expected format: n8n.workflow_name"}}',
                    status=400,
                    mimetype="application/json"
                )
            
            workflow_name = instrument_id.split(".", 1)[1]
            
            # Setup paths
            n8n_base_path = files.get_abs_path("instruments/custom/n8n")
            config_path = Path(n8n_base_path) / "config.json"
            
            # Load existing config
            if not config_path.exists():
                return Response(
                    '{"error": "n8n config.json not found"}',
                    status=404,
                    mimetype="application/json"
                )
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check workflow exists in config
            if workflow_name not in config.get("workflows", {}):
                return Response(
                    f'{{"error": "Workflow \'{workflow_name}\' not found in config.json"}}',
                    status=404,
                    mimetype="application/json"
                )
            
            # Parse webhook URL
            if webhook_url.startswith("http"):
                # Full URL provided - extract base and path
                if "/webhook/" in webhook_url:
                    idx = webhook_url.find("/webhook/")
                    base_url = webhook_url[:idx]
                    webhook_path = webhook_url[idx:]
                    config["n8n_base_url"] = base_url
                    config["workflows"][workflow_name]["webhook_path"] = webhook_path
                elif "/webhook-test/" in webhook_url:
                    # Handle test webhooks
                    idx = webhook_url.find("/webhook-test/")
                    base_url = webhook_url[:idx]
                    webhook_path = webhook_url[idx:]
                    config["n8n_base_url"] = base_url
                    config["workflows"][workflow_name]["webhook_path"] = webhook_path
                else:
                    return Response(
                        '{"error": "Webhook URL must contain \'/webhook/\' or \'/webhook-test/\' path"}',
                        status=400,
                        mimetype="application/json"
                    )
            else:
                # Just path provided - use existing base URL
                webhook_path = webhook_url if webhook_url.startswith("/") else f"/{webhook_url}"
                config["workflows"][workflow_name]["webhook_path"] = webhook_path
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return {
                "success": True,
                "message": f"Webhook URL updated successfully for '{instrument_id}'",
                "instrument_id": instrument_id,
                "workflow_name": workflow_name,
                "webhook_url": f"{config.get('n8n_base_url', '')}{config['workflows'][workflow_name]['webhook_path']}",
                "base_url": config.get("n8n_base_url"),
                "webhook_path": config["workflows"][workflow_name]["webhook_path"]
            }
            
        except json.JSONDecodeError as e:
            return Response(
                f'{{"error": "Invalid JSON in config file: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )
        except Exception as e:
            return Response(
                f'{{"error": "Failed to update webhook URL: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )

