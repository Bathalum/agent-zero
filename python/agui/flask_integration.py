"""
Flask integration for AG-UI server.

Provides a proxy similar to MCP/A2A servers for integration into run_ui.py.
"""

import os
import threading
import json
from typing import Optional
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import Response

from python.agui.config import AGUIConfig
from python.agui.server import AGUIServer
from python.helpers.print_style import PrintStyle

# #region agent log
DEBUG_LOG_PATH = r"c:\Users\alant\OneDrive\Desktop\Projects\agent-zero\.cursor\debug.log"
def _debug_log(location, message, data=None, hypothesis_id=None):
    try:
        log_entry = {
            "location": location,
            "message": message,
            "timestamp": int(__import__("time").time() * 1000),
            "sessionId": "debug-session",
            "runId": "run1"
        }
        if data is not None:
            log_entry["data"] = data
        if hypothesis_id:
            log_entry["hypothesisId"] = hypothesis_id
        log_line = json.dumps(log_entry) + "\n"
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_line)
        # Also print to stderr for immediate visibility
        import sys
        print(f"[DEBUG] {log_line}", file=sys.stderr, end="")
    except Exception as e:
        # Print error to stderr so we know if logging fails
        import sys
        print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
# #endregion


_PRINTER = PrintStyle(italic=True, font_color="cyan", padding=False)


class DynamicAGUIProxy:
    """
    Dynamic proxy for AG-UI server that follows the same pattern as MCP/A2A.
    """
    
    _instance: Optional["DynamicAGUIProxy"] = None
    _lock = threading.RLock()
    
    def __init__(self):
        self.app: Optional[ASGIApp] = None
        self.server: Optional[AGUIServer] = None
        self._initialized = False
    
    @staticmethod
    def get_instance() -> "DynamicAGUIProxy":
        """Get singleton instance."""
        if DynamicAGUIProxy._instance is None:
            with DynamicAGUIProxy._lock:
                if DynamicAGUIProxy._instance is None:
                    DynamicAGUIProxy._instance = DynamicAGUIProxy()
        return DynamicAGUIProxy._instance
    
    def initialize(self):
        """Initialize the AG-UI server if enabled."""
        # #region agent log
        _debug_log("flask_integration.py:initialize", "initialize() called", {
            "initialized": self._initialized
        }, "E")
        # #endregion
        
        if self._initialized:
            return
        
        # Check if AG-UI is enabled (read environment variable)
        enabled = AGUIConfig.is_enabled()
        env_value = os.getenv("AGUI_ENABLED", "not set")
        _PRINTER.print(f"[AG-UI] Environment check: AGUI_ENABLED={env_value}, is_enabled()={enabled}")
        
        # #region agent log
        _debug_log("flask_integration.py:initialize", "Environment check", {
            "AGUI_ENABLED": env_value,
            "is_enabled": enabled
        }, "E")
        # #endregion
        
        if not enabled:
            _PRINTER.print("[AG-UI] Disabled (AGUI_ENABLED not set to true)")
            _PRINTER.print("[AG-UI] To enable: Set AGUI_ENABLED=true in environment and recreate container")
            # Create a minimal ASGI app to handle WebSocket/HTTP requests when disabled
            self.app = self._create_disabled_app()
            # #region agent log
            _debug_log("flask_integration.py:initialize", "Created disabled_app", {
                "app_exists": self.app is not None
            }, "E")
            # #endregion
            self._initialized = True
            return
        
        try:
            # Create server instance
            self.server = AGUIServer.get_instance()
            
            # Start the server
            self.server.start()
            
            # Create ASGI app
            self.app = self.server.create_asgi_app()
            
            _PRINTER.print("[AG-UI] Initialized and ready")
            if AGUIConfig.supports_sse():
                _PRINTER.print("[AG-UI] SSE transport enabled at /agui/sse")
            if AGUIConfig.supports_websocket():
                _PRINTER.print("[AG-UI] WebSocket transport enabled at /agui/ws")
            
            self._initialized = True
            
        except Exception as e:
            _PRINTER.print(f"[AG-UI] Initialization error: {e}")
            # Create a minimal ASGI app to handle requests even on error
            self.app = self._create_disabled_app()
            self._initialized = True  # Mark as initialized to avoid retry loops
    
    def _create_disabled_app(self) -> ASGIApp:
        """Create a minimal ASGI app that handles requests when AG-UI is disabled."""
        async def disabled_app(scope: Scope, receive: Receive, send: Send) -> None:
            # #region agent log
            _debug_log("flask_integration.py:_create_disabled_app", "disabled_app called", {
                "scope_type": scope.get("type"),
                "path": scope.get("path", ""),
                "method": scope.get("method", "")
            }, "B")
            # #endregion
            
            scope_type = scope.get("type")
            
            if scope_type == "websocket":
                # #region agent log
                _debug_log("flask_integration.py:_create_disabled_app", "Sending websocket.close", {
                    "code": 1008,
                    "reason": "AG-UI is disabled"
                }, "B")
                # #endregion
                
                try:
                    # Handle WebSocket connections with proper close frame
                    await send({
                        'type': 'websocket.close',
                        'code': 1008,
                        'reason': 'AG-UI is disabled',
                    })
                    # #region agent log
                    _debug_log("flask_integration.py:_create_disabled_app", "websocket.close sent successfully", {}, "B")
                    # #endregion
                except Exception as e:
                    # #region agent log
                    _debug_log("flask_integration.py:_create_disabled_app", "Exception sending websocket.close", {
                        "error": str(e),
                        "error_type": type(e).__name__
                    }, "B")
                    # #endregion
                    raise
            elif scope_type == "http":
                # Handle HTTP requests with 503 response
                response = {
                    'type': 'http.response.start',
                    'status': 503,
                    'headers': [(b'content-type', b'text/plain')],
                }
                await send(response)
                await send({
                    'type': 'http.response.body',
                    'body': b'AG-UI is disabled or not available',
                })
        
        return disabled_app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Forward ASGI calls to AG-UI app."""
        # #region agent log
        _debug_log("flask_integration.py:__call__", "Proxy __call__ entry", {
            "scope_type": scope.get("type"),
            "path": scope.get("path", ""),
            "method": scope.get("method", ""),
            "initialized": self._initialized,
            "app_exists": self.app is not None
        }, "A")
        # #endregion
        
        scope_type = scope.get("type")
        scope_path = scope.get("path", "")
        scope_method = scope.get("method", "")
        
        _PRINTER.print(f"[AG-UI Proxy] Received request: type={scope_type}, path={scope_path}, method={scope_method}")
        
        # Initialize if not done
        if not self._initialized:
            # #region agent log
            _debug_log("flask_integration.py:__call__", "Calling initialize", {}, "A")
            # #endregion
            self.initialize()
            # #region agent log
            _debug_log("flask_integration.py:__call__", "Initialize completed", {
                "app_exists": self.app is not None,
                "enabled": AGUIConfig.is_enabled()
            }, "A")
            # #endregion
        
        # If AG-UI is disabled or not available, route to disabled app
        if not AGUIConfig.is_enabled() or not self.app:
            # #region agent log
            _debug_log("flask_integration.py:__call__", "Routing to disabled_app", {
                "enabled": AGUIConfig.is_enabled(),
                "app_exists": self.app is not None,
                "scope_type": scope_type
            }, "A")
            # #endregion
            
            _PRINTER.print(f"[AG-UI Proxy] AG-UI disabled or not available. enabled={AGUIConfig.is_enabled()}, app={self.app is not None}")
            
            try:
                # Route to disabled app (which handles WebSocket close and HTTP 503)
                await self.app(scope, receive, send)
                # #region agent log
                _debug_log("flask_integration.py:__call__", "disabled_app completed successfully", {}, "A")
                # #endregion
            except Exception as e:
                # #region agent log
                _debug_log("flask_integration.py:__call__", "Exception in disabled_app", {
                    "error": str(e),
                    "error_type": type(e).__name__
                }, "C")
                # #endregion
                raise
            return
        
        # Strip /agui prefix from path if present (DispatcherMiddleware should strip it, but handle both cases)
        original_path = scope.get("path", "")
        _PRINTER.print(f"[AG-UI Proxy] Received request: path={original_path}, type={scope.get('type')}, method={scope.get('method')}")
        
        if original_path.startswith("/agui/"):
            # Create new scope with modified path
            new_path = original_path[len("/agui"):]
            _PRINTER.print(f"[AG-UI Proxy] Stripping /agui prefix: {original_path} -> {new_path}")
            new_scope = {**scope}
            new_scope["path"] = new_path
            new_scope["raw_path"] = new_path.encode("utf-8")
            scope = new_scope
        elif original_path.startswith("/agui"):
            # Handle /agui without trailing slash
            _PRINTER.print(f"[AG-UI Proxy] Handling /agui root: {original_path} -> /")
            new_scope = {**scope}
            new_scope["path"] = "/"
            new_scope["raw_path"] = b"/"
            scope = new_scope
        else:
            _PRINTER.print(f"[AG-UI Proxy] Path doesn't start with /agui, passing through: {original_path}")
        
        # Route to AG-UI app
        _PRINTER.print(f"[AG-UI Proxy] Forwarding to AG-UI app: path={scope.get('path')}")
        try:
            await self.app(scope, receive, send)
            _PRINTER.print("[AG-UI Proxy] AG-UI app completed")
        except Exception as e:
            _PRINTER.warning(f"[AG-UI Proxy] Error in AG-UI app: {e}")
            import traceback
            _PRINTER.warning(f"[AG-UI Proxy] Traceback: {traceback.format_exc()}")
            raise

