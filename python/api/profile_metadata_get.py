from python.helpers.api import ApiHandler, Request, Response


class ProfileMetadataGet(ApiHandler):
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
            import json
            import os
            from python.helpers import files

            profile_json_path = os.path.join(
                files.get_abs_path("agents", profile_id),
                "profile.json",
            )

            if os.path.exists(profile_json_path):
                with open(profile_json_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    "display_name": profile_id.replace("_", " ").title(),
                    "description": "",
                    "avatar_icon": "default",
                    "avatar_color": "#4A90E2",
                    "category": "General",
                    "enabled_instruments": [],
                    "custom_settings": {},
                }

            return {"success": True, "metadata": metadata}

        except Exception as e:
            return Response(
                f'{{"error": "Failed to load profile metadata: {str(e)}"}}',
                status=500,
                mimetype="application/json",
            )



