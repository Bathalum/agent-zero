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
            # #region agent log
            import json
            import os
            from python.helpers import files
            try:
                DEBUG_LOG_PATH = files.get_abs_path(".cursor", "debug.log")
                os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
                log_entry = {
                    "location": "_20_agui_bridge.py:execute",
                    "message": "Extension called, about to broadcast",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "post-fix",
                    "hypothesisId": "B",
                    "data": {
                        "context_id": context_id,
                        "chunk_length": len(chunk),
                        "full_length": len(full),
                        "message_id": message_id
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception as e:
                import sys
                print(f"[DEBUG LOG ERROR] {e}", file=sys.stderr)
            # #endregion
            
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
                # #region agent log
                try:
                    log_entry = {
                        "location": "_20_agui_bridge.py:execute",
                        "message": "Scheduling broadcast in main event loop (cross-thread)",
                        "timestamp": int(__import__("time").time() * 1000),
                        "sessionId": "debug-session",
                        "runId": "post-fix",
                        "hypothesisId": "B",
                        "data": {
                            "context_id": context_id,
                            "current_loop_id": id(current_loop),
                            "main_loop_id": id(main_loop),
                            "loops_match": current_loop is main_loop
                        }
                    }
                    log_line = json.dumps(log_entry) + "\n"
                    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                        f.write(log_line)
                except Exception:
                    pass
                # #endregion
                
                future = asyncio.run_coroutine_threadsafe(
                    server.broadcast_event(event),
                    main_loop
                )
                # Fire-and-forget: don't wait for completion to avoid blocking extension
                # Optionally log errors if needed
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
                    task = loop.create_task(server.broadcast_event(event))
                    # #region agent log
                    try:
                        log_entry = {
                            "location": "_20_agui_bridge.py:execute",
                            "message": "Task created for broadcast_event (same loop)",
                            "timestamp": int(__import__("time").time() * 1000),
                            "sessionId": "debug-session",
                            "runId": "post-fix",
                            "hypothesisId": "B",
                            "data": {
                                "context_id": context_id,
                                "task_created": True,
                                "loop_id": id(loop)
                            }
                        }
                        log_line = json.dumps(log_entry) + "\n"
                        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                            f.write(log_line)
                    except Exception:
                        pass
                    # #endregion
                except RuntimeError as e:
                    # #region agent log
                    try:
                        log_entry = {
                            "location": "_20_agui_bridge.py:execute",
                            "message": "No running event loop, cannot create task",
                            "timestamp": int(__import__("time").time() * 1000),
                            "sessionId": "debug-session",
                            "runId": "post-fix",
                            "hypothesisId": "B",
                            "data": {
                                "error": str(e),
                                "error_type": type(e).__name__
                            }
                        }
                        log_line = json.dumps(log_entry) + "\n"
                        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                            f.write(log_line)
                    except Exception:
                        pass
                    # #endregion
                    # Fallback: try to await directly (shouldn't happen in async context)
                    await server.broadcast_event(event)
            
            # #region agent log
            try:
                log_entry = {
                    "location": "_20_agui_bridge.py:execute",
                    "message": "broadcast_event called (returned)",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "data": {
                        "context_id": context_id
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                log_entry = {
                    "location": "_20_agui_bridge.py:execute",
                    "message": "Exception in broadcast_event",
                    "timestamp": int(__import__("time").time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "data": {
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                }
                log_line = json.dumps(log_entry) + "\n"
                with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(log_line)
            except Exception:
                pass
            # #endregion
            # Fail silently if AG-UI server is not available
            pass

