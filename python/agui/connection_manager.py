"""
Connection management for AG-UI clients.

Tracks connections per context, manages connection lifecycle,
and provides multi-client support.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import threading


class ConnectionState(Enum):
    """Connection state enumeration."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


@dataclass
class AGUIConnection:
    """Represents an AG-UI client connection."""
    
    connection_id: str
    context_id: str
    transport_type: str  # "sse" or "ws"
    state: ConnectionState = ConnectionState.CONNECTED
    created_at: float = field(default_factory=lambda: __import__("time").time())
    last_activity: float = field(default_factory=lambda: __import__("time").time())
    
    # Transport-specific attributes
    send_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    closed: bool = False
    
    def update_activity(self):
        """Update last activity timestamp."""
        import time
        self.last_activity = time.time()
    
    def mark_disconnected(self):
        """Mark connection as disconnected."""
        self.state = ConnectionState.DISCONNECTED
        self.closed = True
    
    def mark_reconnecting(self):
        """Mark connection as reconnecting."""
        self.state = ConnectionState.RECONNECTING


class ConnectionManager:
    """Manages AG-UI client connections."""
    
    _instance: Optional["ConnectionManager"] = None
    _lock = threading.RLock()
    
    def __init__(self):
        # context_id -> list of connections
        self._connections: Dict[str, List[AGUIConnection]] = {}
        # connection_id -> connection
        self._connection_registry: Dict[str, AGUIConnection] = {}
    
    @classmethod
    def get_instance(cls) -> "ConnectionManager":
        """Get singleton instance of ConnectionManager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def register_connection(
        self,
        context_id: str,
        transport_type: str,
        connection_id: Optional[str] = None
    ) -> AGUIConnection:
        """
        Register a new connection.
        
        Args:
            context_id: The context ID this connection belongs to
            transport_type: "sse" or "ws"
            connection_id: Optional connection ID (generated if not provided)
        
        Returns:
            The created AGUIConnection instance
        """
        if connection_id is None:
            connection_id = str(uuid.uuid4())
        
        connection = AGUIConnection(
            connection_id=connection_id,
            context_id=context_id,
            transport_type=transport_type,
            state=ConnectionState.CONNECTED
        )
        
        with self._lock:
            if context_id not in self._connections:
                self._connections[context_id] = []
            self._connections[context_id].append(connection)
            self._connection_registry[connection_id] = connection
        
        return connection
    
    def unregister_connection(self, connection_id: str):
        """Unregister a connection."""
        with self._lock:
            connection = self._connection_registry.get(connection_id)
            if connection:
                connection.mark_disconnected()
                context_id = connection.context_id
                
                # Remove from context list
                if context_id in self._connections:
                    self._connections[context_id] = [
                        conn for conn in self._connections[context_id]
                        if conn.connection_id != connection_id
                    ]
                    # Clean up empty context entries
                    if not self._connections[context_id]:
                        del self._connections[context_id]
                
                # Remove from registry
                del self._connection_registry[connection_id]
    
    def get_connections(self, context_id: str) -> List[AGUIConnection]:
        """Get all connections for a context."""
        with self._lock:
            return self._connections.get(context_id, []).copy()
    
    def get_connection(self, connection_id: str) -> Optional[AGUIConnection]:
        """Get a connection by ID."""
        with self._lock:
            return self._connection_registry.get(connection_id)
    
    def get_all_connections(self) -> List[AGUIConnection]:
        """Get all active connections."""
        with self._lock:
            return list(self._connection_registry.values())
    
    def cleanup_context(self, context_id: str):
        """Clean up all connections for a context."""
        with self._lock:
            if context_id in self._connections:
                for connection in self._connections[context_id]:
                    connection.mark_disconnected()
                    if connection.connection_id in self._connection_registry:
                        del self._connection_registry[connection.connection_id]
                del self._connections[context_id]
    
    def get_context_ids(self) -> Set[str]:
        """Get all context IDs that have connections."""
        with self._lock:
            return set(self._connections.keys())
    
    def connection_count(self, context_id: Optional[str] = None) -> int:
        """Get connection count, optionally filtered by context."""
        with self._lock:
            if context_id:
                return len(self._connections.get(context_id, []))
            return len(self._connection_registry)

