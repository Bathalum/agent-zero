"""
AG-UI Protocol Server

Main server implementation that handles protocol events, routing,
and coordination between transports, adapters, and connections.
"""

import asyncio
import os
import threading
from typing import Dict, Optional, Any
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import Response
from starlette.requests import Request
from starlette.routing import Route, Mount

from python.agui.config import AGUIConfig
from python.agui.connection_manager import ConnectionManager
from python.agui.transport import SSETransport, WebSocketTransport
from python.agui.adapter import (
    MessageAdapter,
    ResponseAdapter,
    ToolAdapter,
    StateAdapter,
    AGUIEvent,
)
from python.agui.log_bridge import LogBridge
from agent import AgentContext, UserMessage
from python.helpers.print_style import PrintStyle
from python.helpers import runtime


_PRINTER = PrintStyle(italic=True, font_color="cyan", padding=False)


class AGUIServer:
    """Main AG-UI protocol server."""
    
    _instance: Optional["AGUIServer"] = None
    _lock = threading.RLock()
    
    # Protocol version
    PROTOCOL_VERSION = "1.0.0"
    
    # Supported event types
    INCOMING_EVENT_TYPES = {
        "message",
        "tool_call",
        "ping",
        "pong",
    }
    
    OUTGOING_EVENT_TYPES = {
        "connected",
        "message",
        "response",
        "stream_chunk",
        "stream_end",
        "tool_call",
        "tool_result",
        "error",
        "progress",
        "context_state",
        "context_list",
        "notification",
        "log_update",
        "log_reset",
        "agent_action",
    }
    
    def __init__(self):
        self.connection_manager = ConnectionManager.get_instance()
        self.sse_transport = SSETransport(self.connection_manager)
        self.ws_transport = WebSocketTransport(self.connection_manager)
        # Link WebSocket transport to protocol server for message routing
        self.ws_transport.set_protocol_server(self)
        self.log_bridge = LogBridge.get_instance()
        self.log_bridge.set_server(self)
        
        # Event routing
        self._event_handlers: Dict[str, callable] = {
            "message": self._handle_message,
            "tool_call": self._handle_tool_call,
            "ping": self._handle_ping,
            "pong": self._handle_pong,
        }
        
        # Polling task for log updates
        self._polling_task: Optional[asyncio.Task] = None
        self._running = False
    
    @classmethod
    def get_instance(cls) -> "AGUIServer":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def start(self):
        """Start the AG-UI server."""
        if self._running:
            return
        
        self._running = True
        
        # Note: Polling task will be started lazily when first async context is available
        # This avoids "no running event loop" errors during synchronous initialization
        
        _PRINTER.print("[AG-UI] Server started")
    
    def stop(self):
        """Stop the AG-UI server."""
        self._running = False
        
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
        
        _PRINTER.print("[AG-UI] Server stopped")
    
    async def _poll_log_updates(self):
        """Background task to poll for log updates."""
        try:
            while self._running:
                try:
                    self.log_bridge.check_all_contexts()
                    await asyncio.sleep(0.1)  # Poll every 100ms
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Log error but continue polling
                    pass
        except asyncio.CancelledError:
            pass
    
    def broadcast_event(self, event: AGUIEvent):
        """Broadcast an event to all connections in the context."""
        event_dict = event.to_dict()
        
        # Broadcast via SSE
        if AGUIConfig.supports_sse():
            self.sse_transport.broadcast_to_context(
                event.context_id,
                event_dict
            )
        
        # Broadcast via WebSocket
        if AGUIConfig.supports_websocket():
            self.ws_transport.broadcast_to_context(
                event.context_id,
                event_dict
            )
    
    def _ensure_polling_task(self):
        """Ensure polling task is running (called from async context)."""
        if self._running and (self._polling_task is None or self._polling_task.done()):
            try:
                loop = asyncio.get_running_loop()
                self._polling_task = loop.create_task(self._poll_log_updates())
            except RuntimeError:
                # No running loop, task will be created on next async call
                pass
    
    async def handle_incoming_event(
        self,
        connection_id: str,
        event: Dict[str, Any]
    ):
        """Handle an incoming event from a client."""
        # Ensure polling task is started when we have an async context
        self._ensure_polling_task()
        
        event_type = event.get("type")
        context_id = event.get("context_id")
        
        if not context_id:
            connection = self.connection_manager.get_connection(connection_id)
            if connection:
                context_id = connection.context_id
        
        if not context_id:
            return
        
        # Route to appropriate handler
        handler = self._event_handlers.get(event_type)
        if handler:
            try:
                await handler(connection_id, context_id, event)
            except Exception as e:
                # Send error event back
                error_event = ResponseAdapter.error_to_event(
                    str(e),
                    context_id
                )
                self.broadcast_event(error_event)
        else:
            # Unknown event type
            pass
    
    async def _handle_message(
        self,
        connection_id: str,
        context_id: str,
        event: Dict[str, Any]
    ):
        """Handle incoming message event."""
        # Convert AG-UI message to UserMessage
        user_message = MessageAdapter.from_agui_message(event)
        
        # Get or create context
        try:
            from python.api.message import Message
            message_handler = Message(None, None)
            context = message_handler.use_context(context_id, create_if_not_exists=True)
            
            # Log the message
            message_id = event.get("data", {}).get("message_id")
            context.log.log(
                type="user",
                heading="User message",
                content=user_message.message,
                kvps={"attachments": user_message.attachments} if user_message.attachments else None,
                id=message_id,
            )
            
            # Send to agent
            task = context.communicate(user_message)
            # Don't await - let it run asynchronously
            
        except Exception as e:
            error_event = ResponseAdapter.error_to_event(
                f"Failed to process message: {str(e)}",
                context_id,
                event.get("data", {}).get("message_id")
            )
            self.broadcast_event(error_event)
    
    async def _handle_tool_call(
        self,
        connection_id: str,
        context_id: str,
        event: Dict[str, Any]
    ):
        """Handle tool call event."""
        # Tool calls are typically handled by the agent itself
        # This handler can be extended for direct tool execution if needed
        pass
    
    async def _handle_ping(
        self,
        connection_id: str,
        context_id: str,
        event: Dict[str, Any]
    ):
        """Handle ping event."""
        # Respond with pong
        connection = self.connection_manager.get_connection(connection_id)
        if connection:
            pong_event = {
                "type": "pong",
                "context_id": context_id,
                "timestamp": __import__("time").time(),
            }
            
            if connection.transport_type == "sse":
                await self.sse_transport.send_event(connection_id, pong_event)
            elif connection.transport_type == "ws":
                await self.ws_transport.send_event(connection_id, pong_event)
    
    async def _handle_pong(
        self,
        connection_id: str,
        context_id: str,
        event: Dict[str, Any]
    ):
        """Handle pong event."""
        # Update connection activity
        connection = self.connection_manager.get_connection(connection_id)
        if connection:
            connection.update_activity()
    
    def create_asgi_app(self) -> ASGIApp:
        """Create ASGI application with routes for SSE and WebSocket."""
        from starlette.applications import Starlette
        from starlette.routing import Route, WebSocketRoute
        
        routes = []
        
        # SSE endpoint (path will be /sse when mounted at /agui)
        # Note: We can't use Route for ASGI callables that stream, so we'll handle routing manually
        if AGUIConfig.supports_sse():
            self._sse_asgi_app = self.sse_transport.create_asgi_app()
        
        # WebSocket endpoint (path will be /ws when mounted at /agui)
        if AGUIConfig.supports_websocket():
            routes.append(
                WebSocketRoute(
                    "/ws",
                    self.ws_transport.create_asgi_app(),
                )
            )
        
        # Protocol endpoint for receiving events (for WebSocket)
        routes.append(
            Route(
                "/events",
                self._handle_events_endpoint,
                methods=["POST"],
            )
        )
        
        # Create app with routes
        app = Starlette(routes=routes)
        
        # Add CORS middleware for AG-UI endpoints (must be added before wrapping)
        # This is necessary because AG-UI routes are handled by ASGI, not Flask,
        # so Flask-CORS doesn't apply to them
        try:
            from starlette.middleware.cors import CORSMiddleware
            
            # Get allowed origins using same logic as Flask-CORS in run_ui.py
            cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
            
            if cors_origins_env:
                # Production: Use environment variable
                allowed_origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
            elif runtime.is_development():
                # Development: Allow local dev servers
                allowed_origins = [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173"
                ]
            else:
                # Production default: Empty (no CORS if not configured)
                allowed_origins = []
            
            if allowed_origins:
                app.add_middleware(
                    CORSMiddleware,
                    allow_origins=allowed_origins,
                    allow_methods=["GET", "POST", "OPTIONS"],
                    allow_headers=["Content-Type", "X-AGUI-Connection", "X-AGUI-Context"],
                    allow_credentials=False,  # Don't allow credentials for AG-UI
                    max_age=3600
                )
                _PRINTER.print(f"[AG-UI] CORS enabled for origins: {', '.join(allowed_origins)}")
        except ImportError:
            _PRINTER.warning("[AG-UI] starlette CORS middleware not available. CORS disabled for AG-UI endpoints.")
        except Exception as e:
            _PRINTER.warning(f"[AG-UI] Failed to configure CORS: {e}")
        
        # Handle SSE routing manually since it's an ASGI callable that streams
        # We'll intercept requests to /sse and route them to the ASGI app
        original_app = app
        
        async def app_with_sse_routing(scope, receive, send):
            # Debug logging
            scope_type = scope.get("type")
            scope_path = scope.get("path", "")
            scope_method = scope.get("method", "")
            _PRINTER.print(f"[AG-UI] Routing: type={scope_type}, path={scope_path}, method={scope_method}")
            
            # Ensure polling task starts when app is first used (async context available)
            self._ensure_polling_task()
            
            # Check if this is an SSE request
            # Path might be "/sse" (after /agui stripped) or "/agui/sse" (if not stripped)
            is_sse_request = (
                scope_type == "http" and 
                scope_method == "GET" and 
                (scope_path == "/sse" or scope_path.endswith("/sse"))
            )
            
            if is_sse_request:
                _PRINTER.print(f"[AG-UI] Detected SSE request, routing to SSE handler")
                # Route to SSE ASGI app
                if hasattr(self, '_sse_asgi_app'):
                    try:
                        _PRINTER.print(f"[AG-UI] Calling SSE ASGI app")
                        await self._sse_asgi_app(scope, receive, send)
                        _PRINTER.print(f"[AG-UI] SSE ASGI app completed")
                        return
                    except Exception as e:
                        _PRINTER.warning(f"[AG-UI] Error in SSE handler: {e}")
                        import traceback
                        _PRINTER.warning(f"[AG-UI] Traceback: {traceback.format_exc()}")
                        response = Response(f"SSE error: {str(e)}", status_code=500)
                        await response(scope, receive, send)
                        return
                else:
                    _PRINTER.warning(f"[AG-UI] SSE ASGI app not found!")
            else:
                _PRINTER.print(f"[AG-UI] Not SSE request, routing to Starlette app")
            
            # Otherwise, route to normal Starlette app
            try:
                await original_app(scope, receive, send)
            except Exception as e:
                _PRINTER.warning(f"[AG-UI] Error in Starlette app: {e}")
                import traceback
                _PRINTER.warning(f"[AG-UI] Traceback: {traceback.format_exc()}")
                response = Response(f"App error: {str(e)}", status_code=500)
                await response(scope, receive, send)
        
        return app_with_sse_routing
    
    async def _handle_events_endpoint(
        self,
        scope: Scope,
        receive: Receive,
        send: Send
    ):
        """Handle events endpoint for receiving client events."""
        if scope["type"] != "http":
            return
        
        request = Request(scope, receive)
        
        # Check if AG-UI is enabled
        if not AGUIConfig.is_enabled():
            response = Response("AG-UI is disabled", status_code=503)
            await response(scope, receive, send)
            return
        
        try:
            # Get connection_id from header or query
            connection_id = request.headers.get("X-AGUI-Connection") or request.query_params.get("connection_id")
            
            if not connection_id:
                response = Response("connection_id required", status_code=400)
                await response(scope, receive, send)
                return
            
            # Parse event
            event_data = await request.json()
            
            # Handle event
            await self.handle_incoming_event(connection_id, event_data)
            
            response = Response("OK", status_code=200)
            await response(scope, receive, send)
            
        except Exception as e:
            response = Response(f"Error: {str(e)}", status_code=500)
            await response(scope, receive, send)

