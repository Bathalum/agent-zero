from python.helpers.api import ApiHandler, Request, Response


class ProfileConfigGet(ApiHandler):
    """API endpoint for reading profile instruments.json configuration."""
    
    @classmethod
    def requires_auth(cls) -> bool:
        return False
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False
    
    @classmethod
    def requires_api_key(cls) -> bool:
        return False
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Read instruments.json configuration from a profile.
        
        Input:
            profile_id: Profile directory name
        
        Returns:
            success: True if read successfully
            config: Configuration object
            error: Error message if failed
        """
        profile_id = input.get("profile_id")
        
        if not profile_id:
            return Response(
                '{"error": "profile_id is required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            import os
            import json
            from python.helpers import files
            
            instruments_path = files.get_abs_path("agents", profile_id, "instruments.json")
            
            # Return default config if file doesn't exist
            if not os.path.exists(instruments_path):
                default_config = {
                    "enabled": False,
                    "recall_interval": 5,
                    "max_instruments": 2,
                    "similarity_threshold": 0.4,
                    "auto_equip": [],
                    "excluded": [],
                    "filters": {
                        "tags": [],
                        "priority_max": 5
                    }
                }
                return {
                    "success": True,
                    "config": default_config,
                    "exists": False
                }
            
            # Read the configuration
            with open(instruments_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            return {
                "success": True,
                "config": config,
                "exists": True
            }
            
        except json.JSONDecodeError as e:
            return Response(
                f'{{"error": "Invalid JSON in instruments.json: {str(e)}"}}',
                status=400,
                mimetype="application/json"
            )
        except Exception as e:
            return Response(
                f'{{"error": "Failed to read configuration: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )



