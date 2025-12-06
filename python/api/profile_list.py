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
        List available agent profiles with enriched metadata.
        
        Returns information about each profile including:
        - id: Profile directory name
        - name: Human-readable name
        - description: Profile description from _context.md
        - has_extensions: Whether recall extension is present
        - instrument_count: Number of instruments assigned to the profile
        - Optional custom metadata from profile.json (display_name, avatar_icon, etc.)
        """
        try:
            import json
            import os
            from python.helpers.instrument_metadata import InstrumentMetadata

            profile_dirs = files.get_subdirectories("agents", exclude=["_example"])
            
            profiles: list[dict] = []
            for profile_dir in profile_dirs:
                try:
                    # Basic profile info and description from _context.md
                    description = f"{profile_dir} agent profile"
                    context_path = files.get_abs_path("agents", profile_dir, "_context.md")
                    if files.exists(context_path):
                        context = files.read_file(context_path)
                        for line in context.split("\n"):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                description = line
                                break

                    profile_base = {
                        "id": profile_dir,
                        "name": profile_dir.replace("_", " ").title(),
                        "description": description,
                        "has_extensions": self._has_instrument_extensions(profile_dir),
                        "instrument_count": self._count_profile_instruments(profile_dir),
                    }

                    # Load optional custom metadata from profile.json
                    profile_json_path = os.path.join(
                        files.get_abs_path("agents", profile_dir),
                        "profile.json",
                    )

                    if os.path.exists(profile_json_path):
                        with open(profile_json_path, "r", encoding="utf-8") as f:
                            custom_meta = json.load(f)
                        profile_base.update({
                            "display_name": custom_meta.get("display_name", profile_base["name"]),
                            "avatar_icon": custom_meta.get("avatar_icon", "default"),
                            "avatar_color": custom_meta.get("avatar_color", "#4A90E2"),
                            "category": custom_meta.get("category", "General"),
                            "enabled_instruments": custom_meta.get("enabled_instruments", []),
                        })

                    profiles.append(profile_base)

                except Exception:
                    # Fallback for profiles without metadata
                    profiles.append({
                        "id": profile_dir,
                        "name": profile_dir.replace("_", " ").title(),
                        "description": f"{profile_dir} agent profile",
                        "has_extensions": False,
                        "instrument_count": 0,
                    })
            
            profiles.sort(key=lambda p: p["id"])            
            return {"success": True, "profiles": profiles}
            
        except Exception as e:
            return Response(
                f'{{"error": "Failed to list profiles: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )

    def _has_instrument_extensions(self, profile: str) -> bool:
        """Check if profile has instrument recall extensions."""
        import os
        ext_path = files.get_abs_path(
            "agents",
            profile,
            "extensions",
            "message_loop_prompts_after",
            "_55_recall_instruments.py",
        )
        return os.path.exists(ext_path)

    def _count_profile_instruments(self, profile: str) -> int:
        """Count instruments assigned to profile using InstrumentMetadata."""
        try:
            from python.helpers.instrument_metadata import InstrumentMetadata
            instruments = InstrumentMetadata.get_instruments_by_profile(profile)
            return len(instruments)
        except Exception:
            return 0

