from python.helpers.api import ApiHandler, Request, Response


class ProfileSwitch(ApiHandler):
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
        profile_id = input.get("profile_id")
        if not profile_id:
            return Response('{"error": "profile_id required"}', status=400, mimetype="application/json")

        try:
            import os
            from python.helpers import settings, files

            profile_path = files.get_abs_path("agents", profile_id)
            if not os.path.exists(profile_path):
                return Response('{"error": "Profile not found"}', status=404, mimetype="application/json")

            settings.set_settings_delta({"agent_profile": profile_id})

            return {
                "success": True,
                "message": f"Switched to profile: {profile_id}",
                "profile_id": profile_id,
            }

        except Exception as e:
            return Response(
                f'{{"error": "Failed to switch profile: {str(e)}"}}',
                status=500,
                mimetype="application/json",
            )



