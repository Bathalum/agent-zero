from python.helpers.api import ApiHandler, Request, Response
from python.helpers.instrument_metadata import InstrumentMetadata


class ProfileInstruments(ApiHandler):
    """API endpoint for managing instruments assigned to specific profiles."""
    
    @classmethod
    def requires_auth(cls) -> bool:
        return False  # No web auth required
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # No CSRF required
    
    @classmethod
    def requires_api_key(cls) -> bool:
        return False  # No API key required for reading
    
    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Get or modify instruments for a specific profile.
        
        GET (list instruments for profile):
        - profile: str (required) - Profile name
        
        POST (assign/unassign instrument):
        - profile: str (required) - Profile name
        - instrument_id: str (required) - Instrument ID
        - action: "assign" | "unassign" (required) - Action to perform
        """
        method = request.method if hasattr(request, 'method') else 'POST'
        action = input.get("action", "").strip()
        
        # If action is provided, treat as modification (requires API key)
        if action:
            if not self.has_valid_api_key(request):
                return Response(
                    '{"error": "API key required for modifying profile instruments"}',
                    status=401,
                    mimetype="application/json"
                )
        
        profile = input.get("profile", "").strip()
        
        if not profile:
            return Response(
                '{"error": "profile is required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            # Handle read operations (list instruments for profile)
            if not action or action == "list":
                instruments = InstrumentMetadata.get_instruments_by_profile(profile)
                
                return {
                    "success": True,
                    "profile": profile,
                    "instruments": instruments,
                    "count": len(instruments)
                }
            
            # Handle write operations (assign/unassign)
            instrument_id = input.get("instrument_id", "").strip()
            
            if not instrument_id:
                return Response(
                    '{"error": "instrument_id is required for assign/unassign actions"}',
                    status=400,
                    mimetype="application/json"
                )
            
            # Get current instrument metadata
            instrument = InstrumentMetadata.get_instrument_metadata(instrument_id)
            
            if not instrument:
                return Response(
                    f'{{"error": "Instrument \'{instrument_id}\' not found"}}',
                    status=404,
                    mimetype="application/json"
                )
            
            current_profiles = instrument.get("profiles", ["default"])
            
            if action == "assign":
                # Add profile if not already present
                if profile not in current_profiles:
                    current_profiles.append(profile)
                    
                    updated = InstrumentMetadata.update_instrument_metadata(
                        instrument_id,
                        {"profiles": current_profiles}
                    )
                    
                    return {
                        "success": True,
                        "message": f"Instrument '{instrument_id}' assigned to profile '{profile}'",
                        "instrument_id": instrument_id,
                        "profile": profile,
                        "profiles": current_profiles
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Instrument '{instrument_id}' already assigned to profile '{profile}'",
                        "instrument_id": instrument_id,
                        "profile": profile,
                        "profiles": current_profiles
                    }
            
            elif action == "unassign":
                # Remove profile if present
                if profile in current_profiles:
                    current_profiles.remove(profile)
                    
                    # Ensure at least one profile remains (default)
                    if not current_profiles:
                        current_profiles = ["default"]
                    
                    updated = InstrumentMetadata.update_instrument_metadata(
                        instrument_id,
                        {"profiles": current_profiles}
                    )
                    
                    return {
                        "success": True,
                        "message": f"Instrument '{instrument_id}' unassigned from profile '{profile}'",
                        "instrument_id": instrument_id,
                        "profile": profile,
                        "profiles": current_profiles
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Instrument '{instrument_id}' was not assigned to profile '{profile}'",
                        "instrument_id": instrument_id,
                        "profile": profile,
                        "profiles": current_profiles
                    }
            
            else:
                return Response(
                    f'{{"error": "Invalid action \'{action}\'. Use \'assign\' or \'unassign\'"}}',
                    status=400,
                    mimetype="application/json"
                )
                
        except Exception as e:
            return Response(
                f'{{"error": "Failed to process profile instruments: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )
    
    def has_valid_api_key(self, request: Request) -> bool:
        """Check if request has valid API key."""
        try:
            # Get API key from header
            api_key = request.headers.get("X-API-Key", "")
            
            # Basic validation - in production, validate against stored keys
            return bool(api_key and len(api_key) > 0)
        except Exception:
            return False

