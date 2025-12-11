"""
Transport layer for AG-UI protocol.

Supports Server-Sent Events (SSE) and WebSocket transports.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import Response
from starlette.requests import Request

from python.agui.connection_manager import ConnectionManager, AGUIConnection
from python.agui.config import AGUIConfig


class Transport(ABC):
    """Abstract base class for transport implementations."""
    
    @abstractmethod
    async def send_event(self, connection_id: str, event: Dict[str, Any]) -> bool:
        """Send an event to a specific connection."""
        pass
    
    @abstractmethod
    async def broadcast_to_context(self, context_id: str, event: Dict[str, Any]) -> int:
        """Broadcast an event to all connections in a context."""
        pass


class SSETransport(Transport):
    """Server-Sent Events transport implementation."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        # connection_id -> asyncio.Queue for pending messages
        self._message_queues: Dict[str, asyncio.Queue] = {}
        self._keepalive_interval = 30  # seconds
    
    async def send_event(self, connection_id: str, event: Dict[str, Any]) -> bool:
        """Send an event via SSE."""
        if connection_id in self._message_queues:
            try:
                await self._message_queues[connection_id].put(event)
                return True
            except Exception:
                return False
        return False
    
    async def broadcast_to_context(self, context_id: str, event: Dict[str, Any]) -> int:
        """Broadcast event to all SSE connections in a context."""
        connections = self.connection_manager.get_connections(context_id)
        count = 0
        for conn in connections:
            if conn.transport_type == "sse" and not conn.closed:
                if await self.send_event(conn.connection_id, event):
                    count += 1
        return count
    
    async def _handle_sse_connection(
        self,
        connection_id: str,
        context_id: str,
        send: Send
    ):
        """Handle an SSE connection lifecycle."""
        from python.helpers.print_style import PrintStyle
        debug_printer = PrintStyle(italic=True, font_color="cyan", padding=False)
        
        debug_printer.print(f"[SSE Handler] Starting for connection {connection_id}")
        connection = self.connection_manager.get_connection(connection_id)
        if not connection:
            debug_printer.warning(f"[SSE Handler] Connection {connection_id} not found!")
            return
        
        debug_printer.print(f"[SSE Handler] Connection found, creating message queue")
        # Create message queue for this connection
        queue = asyncio.Queue()
        self._message_queues[connection_id] = queue
        
        try:
            debug_printer.print("[SSE Handler] Sending HTTP response start...")
            # Send initial connection event
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [
                    (b'content-type', b'text/event-stream'),
                    (b'cache-control', b'no-cache'),
                    (b'connection', b'keep-alive'),
                    (b'x-accel-buffering', b'no'),  # Disable nginx buffering
                ],
            })
            debug_printer.print("[SSE Handler] HTTP response start sent successfully")
            
            debug_printer.print("[SSE Handler] Sending initial connection message...")
            # Send initial connection confirmation
            await self._send_sse_message(send, {
                "type": "connected",
                "connection_id": connection_id,
                "context_id": context_id,
            })
            debug_printer.print("[SSE Handler] Initial connection message sent")
            
            # Keep-alive task
            last_keepalive = time.time()
            
            while not connection.closed:
                try:
                    # Wait for message or timeout for keepalive
                    timeout = max(1, self._keepalive_interval - (time.time() - last_keepalive))
                    try:
                        event = await asyncio.wait_for(queue.get(), timeout=timeout)
                        await self._send_sse_message(send, event)
                    except asyncio.TimeoutError:
                        # Send keepalive comment
                        await send({
                            'type': 'http.response.body',
                            'body': b': keepalive\n\n',
                            'more_body': True,
                        })
                        last_keepalive = time.time()
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Connection error, break loop
                    break
            
        except Exception:
            pass
        finally:
            # Cleanup
            if connection_id in self._message_queues:
                del self._message_queues[connection_id]
            connection.mark_disconnected()
            self.connection_manager.unregister_connection(connection_id)
    
    async def _send_sse_message(self, send: Send, data: Dict[str, Any]):
        """Send a single SSE message."""
        try:
            json_str = json.dumps(data)
            message = f"data: {json_str}\n\n"
            await send({
                'type': 'http.response.body',
                'body': message.encode('utf-8'),
                'more_body': True,
            })
        except Exception:
            pass
    
    def create_asgi_app(self) -> ASGIApp:
        """Create ASGI application for SSE endpoint."""
        
        async def sse_endpoint(scope: Scope, receive: Receive, send: Send):
            from python.helpers.print_style import PrintStyle
            debug_printer = PrintStyle(italic=True, font_color="cyan", padding=False)
            
            debug_printer.print(f"[SSE] Endpoint called: type={scope.get('type')}, path={scope.get('path')}")
            
            if scope["type"] != "http":
                debug_printer.warning(f"[SSE] Invalid scope type: {scope.get('type')}")
                return
            
            request = Request(scope, receive)
            debug_printer.print(f"[SSE] Request created successfully")
            
            # Check if AG-UI is enabled
            if not AGUIConfig.is_enabled():
                debug_printer.warning("[SSE] AG-UI is disabled")
                response = Response("AG-UI is disabled", status_code=503)
                await response(scope, receive, send)
                return
            
            # Extract context_id from query params or headers
            context_id = request.query_params.get("context_id") or request.headers.get("X-AGUI-Context")
            debug_printer.print(f"[SSE] context_id: {context_id}")
            
            if not context_id:
                debug_printer.warning("[SSE] context_id not provided")
                response = Response("context_id required", status_code=400)
                await response(scope, receive, send)
                return
            
            # Register connection
            debug_printer.print("[SSE] Registering connection...")
            connection = self.connection_manager.register_connection(
                context_id=context_id,
                transport_type="sse"
            )
            debug_printer.print(f"[SSE] Connection registered: {connection.connection_id}")
            
            # Handle the SSE connection
            debug_printer.print("[SSE] Starting SSE connection handler...")
            await self._handle_sse_connection(
                connection.connection_id,
                context_id,
                send
            )
            debug_printer.print("[SSE] SSE connection handler completed")
        
        return sse_endpoint


class WebSocketTransport(Transport):
    """WebSocket transport implementation."""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        # connection_id -> WebSocket send function
        self._websockets: Dict[str, Any] = {}
        self._ping_interval = 30  # seconds
        self._protocol_server = None
    
    async def send_event(self, connection_id: str, event: Dict[str, Any]) -> bool:
        """Send an event via WebSocket."""
        websocket_info = self._websockets.get(connection_id)
        if websocket_info and not websocket_info.get("closed", False):
            try:
                websocket = websocket_info["websocket"]
                await websocket.send_json(event)
                return True
            except Exception:
                websocket_info["closed"] = True
                return False
        return False
    
    async def broadcast_to_context(self, context_id: str, event: Dict[str, Any]) -> int:
        """Broadcast event to all WebSocket connections in a context."""
        connections = self.connection_manager.get_connections(context_id)
        count = 0
        for conn in connections:
            if conn.transport_type == "ws" and not conn.closed:
                if await self.send_event(conn.connection_id, event):
                    count += 1
        return count
    
    def set_protocol_server(self, server):
        """Set the protocol server for routing incoming messages."""
        self._protocol_server = server
    
    async def _handle_websocket_connection(
        self,
        connection_id: str,
        context_id: str,
        websocket: Any
    ):
        """Handle a WebSocket connection lifecycle."""
        connection = self.connection_manager.get_connection(connection_id)
        if not connection:
            return
        
        # Store websocket reference
        self._websockets[connection_id] = {
            "websocket": websocket,
            "closed": False
        }
        
        try:
            # Send initial connection event
            await websocket.send_json({
                "type": "connected",
                "connection_id": connection_id,
                "context_id": context_id,
            })
            
            # Start ping task
            ping_task = asyncio.create_task(
                self._ping_loop(connection_id, websocket)
            )
            
            try:
                # Listen for incoming messages
                while True:
                    try:
                        # Receive message (can be JSON or text)
                        message = await websocket.receive()
                        
                        if message["type"] == "websocket.receive":
                            if "text" in message:
                                try:
                                    data = json.loads(message["text"])
                                    connection.update_activity()
                                    
                                    # Route to protocol server if available
                                    if hasattr(self, "_protocol_server") and self._protocol_server:
                                        await self._protocol_server.handle_incoming_event(
                                            connection_id,
                                            data
                                        )
                                except json.JSONDecodeError:
                                    pass
                            elif "bytes" in message:
                                # Binary messages not supported
                                pass
                                
                    except Exception:
                        break
                        
            finally:
                ping_task.cancel()
                try:
                    await ping_task
                except asyncio.CancelledError:
                    pass
                    
        except Exception:
            pass
        finally:
            # Cleanup
            if connection_id in self._websockets:
                del self._websockets[connection_id]
            connection.mark_disconnected()
            self.connection_manager.unregister_connection(connection_id)
    
    async def _ping_loop(self, connection_id: str, websocket: Any):
        """Send periodic ping messages."""
        try:
            while True:
                await asyncio.sleep(self._ping_interval)
                websocket_info = self._websockets.get(connection_id)
                if not websocket_info or websocket_info.get("closed", False):
                    break
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    websocket_info["closed"] = True
                    break
        except asyncio.CancelledError:
            pass
    
    def create_asgi_app(self) -> ASGIApp:
        """Create ASGI application for WebSocket endpoint."""
        
        async def ws_endpoint(scope: Scope, receive: Receive, send: Send):
            if scope["type"] != "websocket":
                return
            
            # Check if AG-UI is enabled
            if not AGUIConfig.is_enabled():
                # Reject WebSocket connection
                await send({
                    'type': 'websocket.close',
                    'code': 1008,
                    'reason': 'AG-UI is disabled',
                })
                return
            
            # Import WebSocket here to avoid dependency if not needed
            from starlette.websockets import WebSocket
            
            websocket = WebSocket(scope, receive, send)
            await websocket.accept()
            
            # Extract context_id from query params
            context_id = websocket.query_params.get("context_id") or websocket.headers.get("X-AGUI-Context")
            
            if not context_id:
                await websocket.close(code=1008, reason="context_id required")
                return
            
            # Register connection
            connection = self.connection_manager.register_connection(
                context_id=context_id,
                transport_type="ws"
            )
            
            # Handle the WebSocket connection
            await self._handle_websocket_connection(
                connection.connection_id,
                context_id,
                websocket
            )
        
        return ws_endpoint

