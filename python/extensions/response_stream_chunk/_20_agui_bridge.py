"""
AG-UI Bridge Extension

Bridges response stream chunks to AG-UI events for real-time streaming.
"""

from python.helpers.extension import Extension
from agent import LoopData


class AGUIBridge(Extension):
    """
    Bridge extension for AG-UI protocol.
    
    Converts response stream chunks to AG-UI events and broadcasts them
    to connected clients.
    
    Uses lazy imports to avoid loading AG-UI modules when not needed,
    keeping this extension modular and preventing circular import issues.
    """
    
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        """Process stream chunk and broadcast to AG-UI clients."""
        # Lazy import - only load AG-UI modules when needed
        try:
            from python.agui.config import AGUIConfig
            # Check if AG-UI is enabled before importing other modules
            if not AGUIConfig.is_enabled():
                return
        except ImportError:
            # AG-UI not available, fail silently
            return
        
        stream_data = kwargs.get("stream_data")
        if not stream_data:
            return
        
        agent = kwargs.get("agent")
        if not agent or not agent.context:
            return
        
        # Only import these if AG-UI is enabled
        try:
            from python.agui.server import AGUIServer
            from python.agui.adapter import ResponseAdapter
        except ImportError:
            # AG-UI modules not available, fail silently
            return
        
        context_id = agent.context.id
        chunk = stream_data.get("chunk", "")
        full = stream_data.get("full", "")
        
        # Get message_id from loop_data if available
        message_id = None
        if hasattr(loop_data, "params_temporary"):
            log_item = loop_data.params_temporary.get("log_item_response")
            if log_item and hasattr(log_item, "id"):
                message_id = log_item.id
        
        # Create stream event
        event = ResponseAdapter.stream_chunk_to_event(
            chunk=chunk,
            full=full,
            context_id=context_id,
            message_id=message_id
        )
        
        # Broadcast to AG-UI clients
        try:
            server = AGUIServer.get_instance()
            server.broadcast_event(event)
        except Exception:
            # Fail silently if AG-UI server is not available
            pass

