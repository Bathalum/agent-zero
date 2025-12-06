from python.helpers.api import ApiHandler, Request, Response


class ProfileExtensions(ApiHandler):
    """API endpoint for managing profile extensions."""
    
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
        Manage extensions for a profile.
        
        Actions:
            - list: List all extensions in profile
            - get: Read extension file content
            - add: Add/update an extension file
            - remove: Remove an extension file
        
        Input:
            profile_id: Profile directory name
            action: Action to perform (list, get, add, remove)
            extension_path: (for get/add/remove) Relative path within extensions dir
            content: (for add) Extension file content
        
        Returns:
            success: True if successful
            extensions: (for list) List of extension paths
            content: (for get) Extension file content
            error: Error message if failed
        """
        profile_id = input.get("profile_id")
        action = input.get("action")
        
        if not profile_id or not action:
            return Response(
                '{"error": "profile_id and action are required"}',
                status=400,
                mimetype="application/json"
            )
        
        try:
            import os
            from python.helpers import files
            from python.helpers.profile_metadata import is_builtin_profile
            
            if action == "list":
                return await self._list_extensions(profile_id)
            elif action == "get":
                extension_path = input.get("extension_path")
                if not extension_path:
                    return Response(
                        '{"error": "extension_path is required for get action"}',
                        status=400,
                        mimetype="application/json"
                    )
                return await self._get_extension(profile_id, extension_path)
            elif action == "add":
                if is_builtin_profile(profile_id):
                    return Response(
                        '{"error": "Cannot modify built-in profiles"}',
                        status=400,
                        mimetype="application/json"
                    )
                extension_path = input.get("extension_path")
                content = input.get("content", "")
                if not extension_path:
                    return Response(
                        '{"error": "extension_path is required for add action"}',
                        status=400,
                        mimetype="application/json"
                    )
                return await self._add_extension(profile_id, extension_path, content)
            elif action == "remove":
                if is_builtin_profile(profile_id):
                    return Response(
                        '{"error": "Cannot modify built-in profiles"}',
                        status=400,
                        mimetype="application/json"
                    )
                extension_path = input.get("extension_path")
                if not extension_path:
                    return Response(
                        '{"error": "extension_path is required for remove action"}',
                        status=400,
                        mimetype="application/json"
                    )
                return await self._remove_extension(profile_id, extension_path)
            else:
                return Response(
                    '{"error": "Invalid action. Must be: list, get, add, or remove"}',
                    status=400,
                    mimetype="application/json"
                )
                
        except Exception as e:
            return Response(
                f'{{"error": "Failed to manage extensions: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )
    
    async def _list_extensions(self, profile_id: str) -> dict:
        """List all extensions in a profile."""
        import os
        from python.helpers import files
        
        extensions_dir = files.get_abs_path("agents", profile_id, "extensions")
        
        if not os.path.exists(extensions_dir):
            return {"success": True, "extensions": []}
        
        extensions = []
        for root, dirs, files_list in os.walk(extensions_dir):
            for filename in files_list:
                if filename.endswith(".py"):
                    # Get relative path from extensions directory
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, extensions_dir)
                    extensions.append(rel_path.replace("\\", "/"))
        
        return {"success": True, "extensions": sorted(extensions)}
    
    async def _get_extension(self, profile_id: str, extension_path: str) -> dict | Response:
        """Read an extension file."""
        import os
        from python.helpers import files
        
        # Security: prevent directory traversal
        if ".." in extension_path:
            return Response(
                '{"error": "Invalid extension path"}',
                status=400,
                mimetype="application/json"
            )
        
        full_path = files.get_abs_path("agents", profile_id, "extensions", extension_path)
        
        if not os.path.exists(full_path):
            return Response(
                '{"error": "Extension file not found"}',
                status=404,
                mimetype="application/json"
            )
        
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"success": True, "content": content}
    
    async def _add_extension(self, profile_id: str, extension_path: str, content: str) -> dict | Response:
        """Add or update an extension file."""
        import os
        from python.helpers import files
        from python.helpers.profile_metadata import update_profile_metadata
        
        # Security: prevent directory traversal
        if ".." in extension_path:
            return Response(
                '{"error": "Invalid extension path"}',
                status=400,
                mimetype="application/json"
            )
        
        # Ensure it's a Python file
        if not extension_path.endswith(".py"):
            return Response(
                '{"error": "Extension file must be a .py file"}',
                status=400,
                mimetype="application/json"
            )
        
        full_path = files.get_abs_path("agents", profile_id, "extensions", extension_path)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write the file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Update modified timestamp
        from datetime import datetime
        update_profile_metadata(profile_id, {
            "modified_at": datetime.utcnow().isoformat() + "Z"
        })
        
        return {"success": True, "message": "Extension saved successfully"}
    
    async def _remove_extension(self, profile_id: str, extension_path: str) -> dict | Response:
        """Remove an extension file."""
        import os
        from python.helpers import files
        from python.helpers.profile_metadata import update_profile_metadata
        
        # Security: prevent directory traversal
        if ".." in extension_path:
            return Response(
                '{"error": "Invalid extension path"}',
                status=400,
                mimetype="application/json"
            )
        
        full_path = files.get_abs_path("agents", profile_id, "extensions", extension_path)
        
        if not os.path.exists(full_path):
            return Response(
                '{"error": "Extension file not found"}',
                status=404,
                mimetype="application/json"
            )
        
        # Remove the file
        os.remove(full_path)
        
        # Update modified timestamp
        from datetime import datetime
        update_profile_metadata(profile_id, {
            "modified_at": datetime.utcnow().isoformat() + "Z"
        })
        
        return {"success": True, "message": "Extension removed successfully"}



