"""
Bridge between Agent Zero Log system and AG-UI events.

Subscribes to log updates and converts them to AG-UI events for distribution.
"""

import asyncio
import threading
from typing import Dict, Optional, Set
from collections import defaultdict

from agent import AgentContext
from python.agui.connection_manager import ConnectionManager
from python.agui.adapter import ResponseAdapter, AGUIEvent
from python.agui.server import AGUIServer


class LogBridge:
    """
    Bridges Log updates to AG-UI events.
    
    Tracks log versions per context and broadcasts updates to connected clients.
    """
    
    _instance: Optional["LogBridge"] = None
    _lock = threading.RLock()
    
    def __init__(self, server: Optional[AGUIServer] = None):
        self.server = server
        # context_id -> last_log_version
        self._last_versions: Dict[str, int] = {}
        # context_id -> last_log_guid
        self._last_guids: Dict[str, str] = {}
        # context_id -> set of log item IDs we've seen
        self._seen_log_ids: Dict[str, Set[str]] = defaultdict(set)
    
    @classmethod
    def get_instance(cls) -> "LogBridge":
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def set_server(self, server: AGUIServer):
        """Set the AG-UI server instance for event distribution."""
        self.server = server
    
    def subscribe_to_context(self, context_id: str):
        """Subscribe to log updates for a context."""
        with self._lock:
            context = AgentContext.get(context_id)
            if context:
                # Initialize tracking
                self._last_versions[context_id] = len(context.log.updates)
                self._last_guids[context_id] = context.log.guid
                self._seen_log_ids[context_id] = set()
    
    def unsubscribe_from_context(self, context_id: str):
        """Unsubscribe from log updates for a context."""
        with self._lock:
            self._last_versions.pop(context_id, None)
            self._last_guids.pop(context_id, None)
            self._seen_log_ids.pop(context_id, None)
    
    def check_and_broadcast_updates(self, context_id: str) -> bool:
        """
        Check for log updates and broadcast them.
        
        Returns:
            True if updates were found and broadcast, False otherwise
        """
        if not self.server:
            return False
        
        context = AgentContext.get(context_id)
        if not context:
            return False
        
        with self._lock:
            # Check for GUID change (log reset)
            current_guid = context.log.guid
            last_guid = self._last_guids.get(context_id)
            
            if last_guid and current_guid != last_guid:
                # Log was reset, reset tracking
                self._last_versions[context_id] = 0
                self._last_guids[context_id] = current_guid
                self._seen_log_ids[context_id] = set()
                
                # Broadcast reset event
                reset_event = AGUIEvent(
                    type="log_reset",
                    context_id=context_id,
                    data={
                        "log_guid": current_guid,
                    }
                )
                self.server.broadcast_event(reset_event)
                return True
            
            # Check for new log items
            current_version = len(context.log.updates)
            last_version = self._last_versions.get(context_id, 0)
            
            if current_version > last_version:
                # Get new log items
                new_items = context.log.output(start=last_version)
                
                # Broadcast each new item
                for log_item_data in new_items:
                    log_item_no = log_item_data.get("no", -1)
                    log_item_id = log_item_data.get("id")
                    
                    # Check if we've seen this item before (avoid duplicates)
                    item_key = log_item_id or f"no:{log_item_no}"
                    if item_key in self._seen_log_ids[context_id]:
                        continue
                    
                    self._seen_log_ids[context_id].add(item_key)
                    
                    # Get the actual LogItem for conversion
                    if log_item_no >= 0 and log_item_no < len(context.log.logs):
                        log_item = context.log.logs[log_item_no]
                        event = ResponseAdapter.log_item_to_event(log_item, context_id)
                        self.server.broadcast_event(event)
                
                # Update version tracking
                self._last_versions[context_id] = current_version
                self._last_guids[context_id] = current_guid
                return True
        
        return False
    
    def check_all_contexts(self):
        """Check all subscribed contexts for updates."""
        if not self.server:
            return
        
        connection_manager = ConnectionManager.get_instance()
        context_ids = connection_manager.get_context_ids()
        
        for context_id in context_ids:
            self.subscribe_to_context(context_id)  # Ensure subscribed
            self.check_and_broadcast_updates(context_id)

