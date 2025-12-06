from python.helpers.api import ApiHandler, Request, Response


class ProfileMetadataSet(ApiHandler):
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
        metadata = input.get("metadata")

        if not profile_id or not isinstance(metadata, dict):
            return Response('{"error": "profile_id and metadata required"}', status=400, mimetype="application/json")

        try:
            import json
            import os
            from python.helpers import files

            profile_path = files.get_abs_path("agents", profile_id)
            if not os.path.exists(profile_path):
                return Response('{"error": "Profile not found"}', status=404, mimetype="application/json")

            profile_json_path = os.path.join(profile_path, "profile.json")

            if os.path.exists(profile_json_path):
                with open(profile_json_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            else:
                existing = {}

            existing.update(metadata)

            with open(profile_json_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)

            return {"success": True, "metadata": existing}

        except Exception as e:
            return Response(
                f'{{"error": "Failed to update profile metadata: {str(e)}"}}',
                status=500,
                mimetype="application/json",
            )



