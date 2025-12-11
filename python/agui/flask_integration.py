"""
Flask integration for AG-UI server.

Provides a proxy similar to MCP/A2A servers for integration into run_ui.py.
"""

import threading
from typing import Optional
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import Response

from python.agui.config import AGUIConfig
from python.agui.server import AGUIServer
from python.helpers.print_style import PrintStyle


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
        if self._initialized:
            return
        
        if not AGUIConfig.is_enabled():
            _PRINTER.print("[AG-UI] Disabled (AGUI_ENABLED=false)")
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
            self._initialized = True  # Mark as initialized to avoid retry loops
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Forward ASGI calls to AG-UI app."""
        # Initialize if not done
        if not self._initialized:
            self.initialize()
        
        # If AG-UI is disabled or not available
        if not AGUIConfig.is_enabled() or not self.app:
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

