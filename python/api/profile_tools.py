from python.helpers.api import ApiHandler, Request, Response


class ProfileTools(ApiHandler):
    """API endpoint for managing profile custom tools."""
    
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
        Manage custom tools for a profile.
        
        Actions:
            - list: List all tools in profile
            - get: Read tool file content
            - add: Add/update a tool file
            - remove: Remove a tool file
        
        Input:
            profile_id: Profile directory name
            action: Action to perform (list, get, add, remove)
            tool_file: (for get/add/remove) Tool filename
            content: (for add) Tool file content
        
        Returns:
            success: True if successful
            tools: (for list) List of tool filenames
            content: (for get) Tool file content
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
                return await self._list_tools(profile_id)
            elif action == "get":
                tool_file = input.get("tool_file")
                if not tool_file:
                    return Response(
                        '{"error": "tool_file is required for get action"}',
                        status=400,
                        mimetype="application/json"
                    )
                return await self._get_tool(profile_id, tool_file)
            elif action == "add":
                if is_builtin_profile(profile_id):
                    return Response(
                        '{"error": "Cannot modify built-in profiles"}',
                        status=400,
                        mimetype="application/json"
                    )
                tool_file = input.get("tool_file")
                content = input.get("content", "")
                if not tool_file:
                    return Response(
                        '{"error": "tool_file is required for add action"}',
                        status=400,
                        mimetype="application/json"
                    )
                return await self._add_tool(profile_id, tool_file, content)
            elif action == "remove":
                if is_builtin_profile(profile_id):
                    return Response(
                        '{"error": "Cannot modify built-in profiles"}',
                        status=400,
                        mimetype="application/json"
                    )
                tool_file = input.get("tool_file")
                if not tool_file:
                    return Response(
                        '{"error": "tool_file is required for remove action"}',
                        status=400,
                        mimetype="application/json"
                    )
                return await self._remove_tool(profile_id, tool_file)
            else:
                return Response(
                    '{"error": "Invalid action. Must be: list, get, add, or remove"}',
                    status=400,
                    mimetype="application/json"
                )
                
        except Exception as e:
            return Response(
                f'{{"error": "Failed to manage tools: {str(e)}"}}',
                status=500,
                mimetype="application/json"
            )
    
    async def _list_tools(self, profile_id: str) -> dict:
        """List all tools in a profile."""
        import os
        from python.helpers import files
        
        tools_dir = files.get_abs_path("agents", profile_id, "tools")
        
        if not os.path.exists(tools_dir):
            return {"success": True, "tools": []}
        
        tools = []
        for filename in os.listdir(tools_dir):
            if filename.endswith(".py"):
                tools.append(filename)
        
        return {"success": True, "tools": sorted(tools)}
    
    async def _get_tool(self, profile_id: str, tool_file: str) -> dict | Response:
        """Read a tool file."""
        import os
        from python.helpers import files
        
        # Security: prevent directory traversal
        if ".." in tool_file or "/" in tool_file or "\\" in tool_file:
            return Response(
                '{"error": "Invalid tool filename"}',
                status=400,
                mimetype="application/json"
            )
        
        full_path = files.get_abs_path("agents", profile_id, "tools", tool_file)
        
        if not os.path.exists(full_path):
            return Response(
                '{"error": "Tool file not found"}',
                status=404,
                mimetype="application/json"
            )
        
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"success": True, "content": content}
    
    async def _add_tool(self, profile_id: str, tool_file: str, content: str) -> dict | Response:
        """Add or update a tool file."""
        import os
        from python.helpers import files
        from python.helpers.profile_metadata import update_profile_metadata
        
        # Security: prevent directory traversal
        if ".." in tool_file or "/" in tool_file or "\\" in tool_file:
            return Response(
                '{"error": "Invalid tool filename"}',
                status=400,
                mimetype="application/json"
            )
        
        # Ensure it's a Python file
        if not tool_file.endswith(".py"):
            return Response(
                '{"error": "Tool file must be a .py file"}',
                status=400,
                mimetype="application/json"
            )
        
        tools_dir = files.get_abs_path("agents", profile_id, "tools")
        os.makedirs(tools_dir, exist_ok=True)
        
        full_path = os.path.join(tools_dir, tool_file)
        
        # Write the file
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Update modified timestamp
        from datetime import datetime
        update_profile_metadata(profile_id, {
            "modified_at": datetime.utcnow().isoformat() + "Z"
        })
        
        return {"success": True, "message": "Tool saved successfully"}
    
    async def _remove_tool(self, profile_id: str, tool_file: str) -> dict | Response:
        """Remove a tool file."""
        import os
        from python.helpers import files
        from python.helpers.profile_metadata import update_profile_metadata
        
        # Security: prevent directory traversal
        if ".." in tool_file or "/" in tool_file or "\\" in tool_file:
            return Response(
                '{"error": "Invalid tool filename"}',
                status=400,
                mimetype="application/json"
            )
        
        full_path = files.get_abs_path("agents", profile_id, "tools", tool_file)
        
        if not os.path.exists(full_path):
            return Response(
                '{"error": "Tool file not found"}',
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
        
        return {"success": True, "message": "Tool removed successfully"}



