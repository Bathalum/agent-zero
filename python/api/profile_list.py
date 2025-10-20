from python.helpers.api import ApiHandler, Request, Response
from python.helpers import files


class ProfileList(ApiHandler):
    """API endpoint for listing available agent profiles."""
    
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
        List available agent profiles.
        
        Returns information about each profile including:
        - id: Profile directory name
        - name: Human-readable name
        - description: Profile description from _context.md
        """
        try:
            # Get profile directories
            profile_dirs = files.get_subdirectories("agents", exclude=["_example"])
            
            profiles = []
            for profile_dir in profile_dirs:
                # Basic profile info
                profile_info = {
                    "id": profile_dir,
                    "name": profile_dir.replace("_", " ").title(),
                    "description": f"{profile_dir} agent profile"
                }
                
                # Try to get description from _context.md
                try:
                    context_path = files.get_abs_path("agents", profile_dir, "_context.md")
                    if files.exists(context_path):
                        context = files.read_file(context_path)
                        # Get first non-empty line as description
                        for line in context.split("\n"):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                profile_info["description"] = line
                                break
                except Exception:
                    # Use default description if can't read context
                    pass
                
                profiles.append(profile_info)
            
            # Sort profiles alphabetically
            profiles.sort(key=lambda p: p["id"])
            
            return {
                "success": True,
                "profiles": profiles,
                "count": len(profiles)
            }
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to list profiles: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )

