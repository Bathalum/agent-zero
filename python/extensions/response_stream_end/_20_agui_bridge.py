"""
AG-UI Bridge Extension for Stream End

Finalizes response streams and sends completion events to AG-UI clients.
"""

from python.helpers.extension import Extension
from agent import LoopData


class AGUIBridgeEnd(Extension):
    """
    Bridge extension for AG-UI protocol stream completion.
    
    Sends stream end events to connected AG-UI clients when response
    streaming is complete.
    
    Uses lazy imports to avoid loading AG-UI modules when not needed,
    keeping this extension modular and preventing circular import issues.
    """
    
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        """Process stream end and broadcast completion event."""
        # Lazy import - only load AG-UI modules when needed
        try:
            from python.agui.config import AGUIConfig
            # Check if AG-UI is enabled before importing other modules
            if not AGUIConfig.is_enabled():
                return
        except ImportError:
            # AG-UI not available, fail silently
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
        
        # Get message_id and final text from loop_data if available
        message_id = None
        final_text = None
        if hasattr(loop_data, "params_temporary"):
            log_item = loop_data.params_temporary.get("log_item_response")
            if log_item:
                if hasattr(log_item, "id"):
                    message_id = log_item.id
                if hasattr(log_item, "content"):
                    final_text = log_item.content
        
        # Create stream end event
        event = ResponseAdapter.stream_end_to_event(
            context_id=context_id,
            message_id=message_id,
            final_text=final_text
        )
        
        # Broadcast to AG-UI clients
        try:
            import asyncio
            server = AGUIServer.get_instance()
            
            # Get the main event loop (where SSE connections are managed)
            # Extensions run in DeferredTask's event loop (separate thread),
            # but broadcast_event() must run in the main event loop
            main_loop = server.get_main_event_loop()
            current_loop = None
            try:
                current_loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            
            # Check if we're in the main loop or a different loop
            if main_loop and current_loop and current_loop is not main_loop:
                # We're in a different event loop (DeferredTask thread)
                # Use run_coroutine_threadsafe to schedule in the main loop
                future = asyncio.run_coroutine_threadsafe(
                    server.broadcast_event(event),
                    main_loop
                )
                # Fire-and-forget: don't wait for completion to avoid blocking extension
                try:
                    # Set a short timeout to check for immediate errors
                    future.result(timeout=0.1)
                except Exception:
                    # Timeout or error is OK - event is scheduled
                    pass
            else:
                # We're in the main loop or no main loop captured yet
                # Try to schedule normally
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(server.broadcast_event(event))
                except RuntimeError:
                    # Fallback: await directly if no running loop (shouldn't happen)
                    await server.broadcast_event(event)
        except Exception:
            # Fail silently if AG-UI server is not available
            pass

