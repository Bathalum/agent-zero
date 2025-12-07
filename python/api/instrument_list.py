from python.helpers.api import ApiHandler, Request, Response
from python.helpers.instrument_metadata import InstrumentMetadata
from python.helpers import files
import os
import json


class InstrumentList(ApiHandler):
    """API endpoint for listing registered instruments with optional filtering."""
    
    @classmethod
    def requires_auth(cls) -> bool:
        return False  # No web auth required
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # No CSRF required
    
    @classmethod
    def requires_api_key(cls) -> bool:
        return False  # No API key required for listing
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        List registered instruments with optional filtering.
        
        Query parameters:
        - profile: Filter by profile name (optional)
        - tags: Filter by tags, comma-separated (optional)
        - enabled: Filter by enabled status, "true" or "false" (optional)
        - type: Filter by instrument type, e.g., "n8n" (optional)
        """
        try:
            # Get filter parameters
            profile_filter = input.get("profile", "").strip()
            tags_filter = input.get("tags", "").strip()
            enabled_filter = input.get("enabled", "").strip()
            type_filter = input.get("type", "").strip()
            
            # Start with all instruments
            if profile_filter:
                instruments = InstrumentMetadata.get_instruments_by_profile(profile_filter)
            else:
                instruments = InstrumentMetadata.list_all_instruments()
            
            # Apply tags filter if provided
            if tags_filter:
                tags_list = [tag.strip() for tag in tags_filter.split(",") if tag.strip()]
                if tags_list:
                    instruments = [
                        inst for inst in instruments
                        if any(tag in inst.get("tags", []) for tag in tags_list)
                    ]
            
            # Apply enabled filter if provided
            if enabled_filter:
                if enabled_filter.lower() == "true":
                    instruments = [inst for inst in instruments if inst.get("enabled", True)]
                elif enabled_filter.lower() == "false":
                    instruments = [inst for inst in instruments if not inst.get("enabled", True)]
            
            # Apply type filter if provided
            if type_filter:
                instruments = [inst for inst in instruments if inst.get("type", "") == type_filter]
            
            # Enrich with additional information (like description from .md file)
            enriched_instruments = []
            for inst in instruments:
                enriched = inst.copy()
                
                # Try to read description from source file
                source_path = inst.get("source_path", "")
                if source_path and os.path.exists(files.get_abs_path(source_path)):
                    try:
                        content = files.read_file(files.get_abs_path(source_path))
                        # Extract first line after "# Problem" header
                        lines = content.split("\n")
                        for i, line in enumerate(lines):
                            if line.strip().startswith("# Problem"):
                                if i + 1 < len(lines):
                                    enriched["description"] = lines[i + 1].strip()
                                    break
                        
                        # If no description found, use display_name
                        if "description" not in enriched:
                            enriched["description"] = inst.get("metadata", {}).get("display_name", inst.get("id", ""))
                    except Exception:
                        enriched["description"] = inst.get("metadata", {}).get("display_name", inst.get("id", ""))
                else:
                    enriched["description"] = inst.get("metadata", {}).get("display_name", inst.get("id", ""))
                
                # Add display_name from nested metadata if available
                if "metadata" in inst and "display_name" in inst["metadata"]:
                    enriched["display_name"] = inst["metadata"]["display_name"]
                else:
                    # Generate from ID
                    enriched["display_name"] = inst.get("id", "").replace("_", " ").replace(".", " ").title()
                
                # For n8n instruments, add webhook URL information
                if inst.get("type") == "n8n":
                    try:
                        # Extract workflow name from instrument_id (e.g., "n8n.slack_message" -> "slack_message")
                        workflow_name = inst.get("id", "").split(".", 1)[1] if "." in inst.get("id", "") else ""
                        if workflow_name:
                            config_path = files.get_abs_path("instruments/custom/n8n/config.json")
                            if os.path.exists(config_path):
                                with open(config_path, 'r') as f:
                                    n8n_config = json.load(f)
                                
                                workflow_config = n8n_config.get("workflows", {}).get(workflow_name, {})
                                base_url = n8n_config.get("n8n_base_url", "")
                                webhook_path = workflow_config.get("webhook_path", "")
                                
                                if base_url and webhook_path:
                                    enriched["webhook_url"] = f"{base_url}{webhook_path}"
                                    enriched["webhook_path"] = webhook_path
                                    enriched["n8n_base_url"] = base_url
                    except Exception:
                        # Silently fail if we can't read webhook info
                        pass
                
                enriched_instruments.append(enriched)
            
            return {
                "success": True,
                "instruments": enriched_instruments,
                "count": len(enriched_instruments),
                "filters": {
                    "profile": profile_filter if profile_filter else None,
                    "tags": tags_list if tags_filter else None,
                    "enabled": enabled_filter if enabled_filter else None,
                    "type": type_filter if type_filter else None,
                }
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to list instruments: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )

