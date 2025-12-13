"""
AG-UI Protocol Server

Main server implementation that handles protocol events, routing,
and coordination between transports, adapters, and connections.
"""

import asyncio
import json
import os
import threading
from typing import Dict, Optional, Any
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import Response
from starlette.requests import Request
from starlette.routing import Route, Mount

from python.agui.config import AGUIConfig
from python.agui.connection_manager import ConnectionManager, ConnectionState
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
        
        # Main event loop reference (for cross-thread event broadcasting)
        # This will be set when the first async operation runs in the main event loop
        self._main_event_loop: Optional[asyncio.AbstractEventLoop] = None
    
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
        
        # Try to capture the main event loop if one is running
        try:
            self._main_event_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop yet, will be set when first async operation runs
            pass
        
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
                    await self.log_bridge.check_all_contexts()
                    await asyncio.sleep(0.1)  # Poll every 100ms
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Log error but continue polling
                    pass
        except asyncio.CancelledError:
            pass
    
    async def broadcast_event(self, event: AGUIEvent):
        """Broadcast an event to all connections in the context."""
        # #region agent log
        import json
        import os
        from python.helpers import files
        try:
            DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            event_dict_preview = event.to_dict() if hasattr(event, 'to_dict') else {}
            log_entry = {
                "location": "server.py:broadcast_event",
                "message": "broadcast_event called (async)",
                "timestamp": int(__import__("time").time() * 1000),
                "sessionId": "debug-session",
                "runId": "post-fix",
                "hypothesisId": "A",
                "data": {
                    "event_type": event.type if hasattr(event, 'type') else 'unknown',
                    "context_id": event.context_id if hasattr(event, 'context_id') else 'unknown',
                    "supports_sse": AGUIConfig.supports_sse(),
                    "supports_ws": AGUIConfig.supports_websocket(),
                    "event_data_preview": event_dict_preview.get("data", {})
                }
            }
            log_line = json.dumps(log_entry) + "\n"
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            import sys
            print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
        # #endregion
        
        event_dict = event.to_dict()
        
        # Broadcast via SSE
        if AGUIConfig.supports_sse():
            # #region agent log
            try:
                log_entry = {
                    "location": "server.py:broadcast_event",
                    "message": "Calling SSE broadcast_to_context (AWAITING)",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "post-fix",
                    "hypothesisId": "A",
                    "data": {
                        "context_id": event.context_id,
                        "event_type": event_dict.get("type", "unknown")
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
            
            count = await self.sse_transport.broadcast_to_context(
                event.context_id,
                event_dict
            )
            
            # #region agent log
            try:
                log_entry = {
                    "location": "server.py:broadcast_event",
                    "message": "SSE broadcast_to_context completed",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "post-fix",
                    "hypothesisId": "A",
                    "data": {
                        "events_sent": count
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
        
        # Broadcast via WebSocket
        if AGUIConfig.supports_websocket():
            await self.ws_transport.broadcast_to_context(
                event.context_id,
                event_dict
            )
    
    def _ensure_polling_task(self):
        """Ensure polling task is running (called from async context)."""
        if self._running and (self._polling_task is None or self._polling_task.done()):
            try:
                loop = asyncio.get_running_loop()
                # Store main event loop reference for cross-thread broadcasting
                if self._main_event_loop is None:
                    self._main_event_loop = loop
                self._polling_task = loop.create_task(self._poll_log_updates())
            except RuntimeError:
                # No running loop, task will be created on next async call
                pass
    
    def get_main_event_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """
        Get the main event loop reference for cross-thread event broadcasting.
        
        Returns None if no main event loop has been captured yet.
        """
        # Try to get current running loop if we don't have one stored
        if self._main_event_loop is None:
            try:
                self._main_event_loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
        return self._main_event_loop
    
    async def handle_incoming_event(
        self,
        connection_id: str,
        event: Dict[str, Any]
    ):
        """Handle an incoming event from a client."""
        # #region agent log
        import json
        import os
        from python.helpers import files
        try:
            DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            log_entry = {
                "location": "server.py:handle_incoming_event",
                "message": "handle_incoming_event called",
                "timestamp": int(__import__("time").time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "D",
                "data": {
                    "connection_id": connection_id,
                    "event_type": event.get("type"),
                    "event_context_id": event.get("context_id")
                }
            }
            log_line = json.dumps(log_entry) + "\n"
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            import sys
            print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
        # #endregion
        
        # Ensure polling task is started when we have an async context
        self._ensure_polling_task()
        
        event_type = event.get("type")
        
        # Prioritize connection's context_id when connection_id is provided
        # This ensures events are broadcast to the correct SSE connection
        context_id = None
        connection = None
        if connection_id:
            connection = self.connection_manager.get_connection(connection_id)
            if connection:
                context_id = connection.context_id
                # Update event with connection's context_id to ensure consistency
                event["context_id"] = context_id
        
        # Fallback to event's context_id if connection not found or no connection_id provided
        if not context_id:
            context_id = event.get("context_id")
            
            # If still no context_id, try to get it from connection lookup
            if not context_id and connection_id:
                # #region agent log
                try:
                    DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                    os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                    log_entry = {
                        "location": "server.py:handle_incoming_event",
                        "message": "Looking up connection to get context_id",
                        "timestamp": int(__import__("time").time() * 1000),
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "data": {
                            "connection_id": connection_id
                        }
                    }
                    log_line = json.dumps(log_entry) + "\n"
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                        f.write(log_line)
                except Exception:
                    pass
                # #endregion
                
                if not connection:
                    connection = self.connection_manager.get_connection(connection_id)
                
                # #region agent log
                try:
                    DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                    os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                    log_entry = {
                        "location": "server.py:handle_incoming_event",
                        "message": "Connection lookup result",
                        "timestamp": int(__import__("time").time() * 1000),
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "data": {
                            "connection_id": connection_id,
                            "connection_found": connection is not None,
                            "connection_type": type(connection).__name__ if connection else None,
                            "connection_context_id": connection.context_id if connection else None
                        }
                    }
                    log_line = json.dumps(log_entry) + "\n"
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                        f.write(log_line)
                except Exception:
                    pass
                # #endregion
                
                if connection:
                    context_id = connection.context_id
                    event["context_id"] = context_id
        
        if not context_id:
            # #region agent log
            try:
                DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                log_entry = {
                    "location": "server.py:handle_incoming_event",
                    "message": "No context_id found, returning early",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "F",
                    "data": {
                        "connection_id": connection_id,
                        "event_context_id": event.get("context_id")
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
            return
        
        # Route to appropriate handler
        handler = self._event_handlers.get(event_type)
        if handler:
            try:
                await handler(connection_id, context_id, event)
            except Exception as e:
                # #region agent log
                try:
                    DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                    os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                    import traceback
                    log_entry = {
                        "location": "server.py:handle_incoming_event",
                        "message": "Exception in event handler",
                        "timestamp": int(__import__("time").time() * 1000),
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "G",
                        "data": {
                            "connection_id": connection_id,
                            "context_id": context_id,
                            "event_type": event_type,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "traceback": traceback.format_exc()
                        }
                    }
                    log_line = json.dumps(log_entry) + "\n"
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                        f.write(log_line)
                except Exception:
                    pass
                # #endregion
                
                # Send error event back
                error_event = ResponseAdapter.error_to_event(
                    str(e),
                    context_id
                )
                # Schedule broadcast as a task (fire-and-forget)
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.broadcast_event(error_event))
                except RuntimeError:
                    # Fallback: await directly if no running loop (shouldn't happen in async context)
                    await self.broadcast_event(error_event)
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
        # #region agent log
        import json
        import os
        from python.helpers import files
        try:
            DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            log_entry = {
                "location": "server.py:_handle_message",
                "message": "_handle_message called",
                "timestamp": int(__import__("time").time() * 1000),
                "sessionId": "debug-session",
                "runId": "post-fix",
                "hypothesisId": "B",
                "data": {
                    "connection_id": connection_id,
                    "context_id": context_id,
                    "event_type": event.get("type", "unknown")
                }
            }
            log_line = json.dumps(log_entry) + "\n"
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            import sys
            print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
        # #endregion
        
        # Convert AG-UI message to UserMessage
        user_message = MessageAdapter.from_agui_message(event)
        
        # Get or create context
        try:
            from python.api.message import Message
            import threading
            # Create a lock for thread safety (Message requires thread_lock parameter)
            thread_lock = threading.Lock()
            message_handler = Message(None, thread_lock)
            context = message_handler.use_context(context_id, create_if_not_exists=True)
            
            # #region agent log
            try:
                log_entry = {
                    "location": "server.py:_handle_message",
                    "message": "Context obtained, logging message",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "data": {
                        "context_id": context_id,
                        "context_exists": context is not None,
                        "context_type": type(context).__name__ if context else None
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
            
            # Validate context exists before using it
            if context is None:
                raise ValueError(f"Failed to get or create context for context_id: {context_id}")
            
            # Log the message
            message_id = event.get("data", {}).get("message_id")
            context.log.log(
                type="user",
                heading="User message",
                content=user_message.message,
                kvps={"attachments": user_message.attachments} if user_message.attachments else None,
                id=message_id,
            )
            
            # #region agent log
            try:
                log_entry = {
                    "location": "server.py:_handle_message",
                    "message": "Calling context.communicate (not awaited)",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "data": {
                        "context_id": context_id,
                        "message_length": len(user_message.message)
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
            
            # Send to agent
            task = context.communicate(user_message)
            # Don't await - let it run asynchronously
            
        except Exception as e:
            # #region agent log
            try:
                DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                log_entry = {
                    "location": "server.py:_handle_message",
                    "message": "Exception in _handle_message",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "D",
                    "data": {
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "error_repr": repr(e),
                        "error_str_empty": len(str(e)) == 0,
                        "error_str_length": len(str(e)),
                        "has_args": hasattr(e, "__args__"),
                        "args": list(e.__args__) if hasattr(e, "__args__") else None
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception as log_err:
                import sys
                print(f"[DEBUG LOG ERROR] {log_err}", file=sys.stderr)
            # #endregion
            
            error_event = ResponseAdapter.error_to_event(
                f"Failed to process message: {str(e)}",
                context_id,
                event.get("data", {}).get("message_id")
            )
            
            # #region agent log
            try:
                DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                event_dict = error_event.to_dict()
                event_data = event_dict.get("data", {})
                log_entry = {
                    "location": "server.py:_handle_message",
                    "message": "About to broadcast error event",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "data": {
                        "error_event_dict": event_dict,
                        "error_event_data": event_data,
                        "error_event_data_keys": list(event_data.keys()) if event_data else [],
                        "has_error_field": "error" in event_data,
                        "error_value": event_data.get("error", "MISSING"),
                        "error_value_type": type(event_data.get("error", None)).__name__ if event_data.get("error") else "None",
                        "error_value_length": len(str(event_data.get("error", ""))) if event_data.get("error") else 0,
                        "exception_str": str(e),
                        "exception_type": type(e).__name__,
                        "full_event_json": json.dumps(event_dict)
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception as log_err:
                import sys
                print(f"[DEBUG LOG ERROR] {log_err}", file=sys.stderr)
            # #endregion
            
            # Schedule broadcast as a task (fire-and-forget)
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.broadcast_event(error_event))
            except RuntimeError:
                # Fallback: await directly if no running loop (shouldn't happen in async context)
                await self.broadcast_event(error_event)
    
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
        from starlette.responses import JSONResponse
        
        routes = []
        
        # Status endpoint (GET /agui) - allows frontend to check if AG-UI is enabled
        async def status_endpoint(request):
            """Return AG-UI status information."""
            if not AGUIConfig.is_enabled():
                return JSONResponse(
                    {"enabled": False, "message": "AG-UI is disabled"},
                    status_code=503
                )
            
            return JSONResponse({
                "enabled": True,
                "message": "AG-UI is enabled and ready",
                "transports": {
                    "sse": AGUIConfig.supports_sse(),
                    "websocket": AGUIConfig.supports_websocket(),
                },
                "endpoints": {
                    "sse": "/agui/sse",
                    "websocket": "/agui/ws",
                    "events": "/agui/events",
                }
            })
        
        routes.append(
            Route(
                "/",
                status_endpoint,
                methods=["GET"],
            )
        )
        
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
            else:
                # Development: Auto-allow localhost origins if CORS_ALLOWED_ORIGINS not set
                # This matches the behavior documented in the contract
                # When CORS_ALLOWED_ORIGINS is not set, auto-allow localhost for development
                allowed_origins = [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:5173"
                ]
            
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
            
            # Check if this is a WebSocket upgrade request (HTTP GET with Upgrade header)
            # a2wsgi doesn't convert WebSocket upgrades, so we need to handle them manually
            is_websocket_upgrade = (
                scope_type == "http" and 
                scope_method == "GET" and 
                (scope_path == "/ws" or scope_path.endswith("/ws"))
            )
            
            if is_websocket_upgrade:
                # Check for Upgrade header (ASGI headers are list of tuples)
                upgrade_header = None
                for header_name, header_value in scope.get("headers", []):
                    if header_name.lower() == b"upgrade":
                        upgrade_header = header_value.decode("utf-8").lower()
                        break
                
                if upgrade_header == "websocket":
                    _PRINTER.print(f"[AG-UI] Detected WebSocket upgrade request")
                    
                    if not AGUIConfig.is_enabled():
                        # AG-UI disabled - send HTTP 503
                        response = Response("AG-UI is disabled", status_code=503)
                        await response(scope, receive, send)
                        return
                    
                    if not (hasattr(self, 'ws_transport') and AGUIConfig.supports_websocket()):
                        # WebSocket transport not available - send HTTP 503
                        response = Response("WebSocket transport not enabled", status_code=503)
                        await response(scope, receive, send)
                        return
                    
                    # CRITICAL: a2wsgi doesn't support WebSocket with Werkzeug's WSGI server
                    # WSGI is HTTP-only and cannot handle WebSocket protocol after handshake
                    # We need to reject WebSocket upgrades and recommend SSE instead
                    _PRINTER.warning("[AG-UI] WebSocket upgrade rejected: a2wsgi/Werkzeug doesn't support WebSocket")
                    _PRINTER.warning("[AG-UI] Use SSE transport instead (transport: 'sse' in client config)")
                    
                    # Send HTTP 503 to trigger frontend fallback to SSE
                    # Frontend should automatically fall back to SSE when WebSocket fails
                    response = Response(
                        "WebSocket not supported with WSGI server. Use SSE transport.",
                        status_code=503
                    )
                    await response(scope, receive, send)
                    return
            
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
                _PRINTER.print(f"[AG-UI] Not SSE/WebSocket request, routing to Starlette app")
            
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
    
    async def _handle_events_endpoint(self, request: Request):
        """Handle events endpoint for receiving client events."""
        # #region agent log
        import json
        import os
        from python.helpers import files
        try:
            DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
            os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
            log_entry = {
                "location": "server.py:_handle_events_endpoint",
                "message": "_handle_events_endpoint called",
                "timestamp": int(__import__("time").time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "data": {
                    "method": request.method,
                    "path": request.url.path
                }
            }
            log_line = json.dumps(log_entry) + "\n"
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            import sys
            print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
        # #endregion
        
        # Log request details for debugging
        method = request.method
        path = request.url.path
        origin = request.headers.get("origin")
        
        _PRINTER.print(f"[AG-UI Events] {method} {path} - Origin: {origin}")
        
        # Check if AG-UI is enabled
        if not AGUIConfig.is_enabled():
            _PRINTER.warning("[AG-UI Events] AG-UI is disabled")
            return Response("AG-UI is disabled", status_code=503)
        
        try:
            # Get connection_id from header or query (optional)
            connection_id = request.headers.get("X-AGUI-Connection") or request.query_params.get("connection_id")
            
            # #region agent log
            try:
                DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                log_entry = {
                    "location": "server.py:_handle_events_endpoint",
                    "message": "Extracted connection_id from headers",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "data": {
                        "connection_id": connection_id,
                        "header_value": request.headers.get("X-AGUI-Connection"),
                        "query_value": request.query_params.get("connection_id")
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
            
            # Parse event
            event_data = await request.json()
            
            # Get context_id - prioritize connection's context_id if connection_id is provided
            # This ensures events are broadcast to the correct SSE connection
            context_id = None
            if connection_id:
                # Look up connection to get its context_id
                connection = self.connection_manager.get_connection(connection_id)
                if connection:
                    context_id = connection.context_id
                    _PRINTER.print(f"[AG-UI Events] Using context_id from connection: {context_id}")
            
            # Fallback to event data or header if connection_id not provided or connection not found
            if not context_id:
                context_id = (
                    event_data.get("context_id") or 
                    request.headers.get("X-AGUI-Context") or 
                    request.query_params.get("context_id")
                )
            
            # #region agent log
            try:
                DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                log_entry = {
                    "location": "server.py:_handle_events_endpoint",
                    "message": "Extracted context_id",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "data": {
                        "context_id": context_id,
                        "connection_id": connection_id,
                        "event_context_id": event_data.get("context_id"),
                        "header_context_id": request.headers.get("X-AGUI-Context"),
                        "query_context_id": request.query_params.get("context_id"),
                        "connection_found": connection is not None if connection_id else None,
                        "connection_context_id": connection.context_id if connection_id and connection else None
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
            
            # Ensure event_data has the correct context_id for processing
            if context_id:
                event_data["context_id"] = context_id
            
            # If connection_id not provided, try to find it from context_id
            if not connection_id and context_id:
                # Get first active connection for this context
                connections = self.connection_manager.get_connections(context_id)
                active_connections = [c for c in connections if not c.closed and c.state == ConnectionState.CONNECTED]
                
                # #region agent log
                try:
                    DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                    os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                    log_entry = {
                        "location": "server.py:_handle_events_endpoint",
                        "message": "Looking up connection from context_id",
                        "timestamp": int(__import__("time").time() * 1000),
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "data": {
                            "context_id": context_id,
                            "total_connections": len(connections),
                            "active_connections": len(active_connections),
                            "connection_ids": [c.connection_id for c in active_connections]
                        }
                    }
                    log_line = json.dumps(log_entry) + "\n"
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                        f.write(log_line)
                except Exception:
                    pass
                # #endregion
                
                if active_connections:
                    connection_id = active_connections[0].connection_id
                    _PRINTER.print(f"[AG-UI Events] Found connection_id from context: {connection_id} for context: {context_id}")
                else:
                    _PRINTER.print(f"[AG-UI Events] No active connections found for context: {context_id}")
            
            # Validate that we have either connection_id or context_id
            if not connection_id and not context_id:
                return Response(
                    "Either connection_id (X-AGUI-Connection header) or context_id (in event or X-AGUI-Context header) is required",
                    status_code=400
                )
            
            # If we have context_id but no connection_id, we can still process the event
            # The event handlers can work with just context_id for broadcasting
            if not connection_id:
                _PRINTER.print(f"[AG-UI Events] Processing event without connection_id, using context_id: {context_id}")
                # We'll use context_id as a fallback - handlers will broadcast to all connections in context
                connection_id = context_id
            
            # #region agent log
            try:
                DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                # Look up connection to verify it exists
                connection = self.connection_manager.get_connection(connection_id)
                log_entry = {
                    "location": "server.py:_handle_events_endpoint",
                    "message": "Before calling handle_incoming_event",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "C",
                    "data": {
                        "connection_id": connection_id,
                        "connection_exists": connection is not None,
                        "connection_type": type(connection).__name__ if connection else None,
                        "connection_context_id": connection.context_id if connection else None,
                        "connection_closed": connection.closed if connection else None
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception as e:
                import sys
                print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
            # #endregion
            
            # Handle event
            await self.handle_incoming_event(connection_id, event_data)
            
            return Response("OK", status_code=200)
            
        except json.JSONDecodeError as e:
            _PRINTER.warning(f"[AG-UI Events] JSON decode error: {e}")
            return Response(f"Invalid JSON: {str(e)}", status_code=400)
        except Exception as e:
            _PRINTER.warning(f"[AG-UI Events] Error processing event: {e}")
            import traceback
            _PRINTER.warning(f"[AG-UI Events] Traceback: {traceback.format_exc()}")
            return Response(f"Error: {str(e)}", status_code=500)

