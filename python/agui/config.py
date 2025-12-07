"""
Configuration management for AG-UI integration.
"""

import os
from typing import Literal
from python.helpers import dotenv


class AGUIConfig:
    """Configuration for AG-UI integration."""

    # Default values
    DEFAULT_ENABLED = False
    DEFAULT_TRANSPORT = "both"  # "sse", "ws", or "both"
    DEFAULT_AUTH_REQUIRED = False

    @staticmethod
    def is_enabled() -> bool:
        """Check if AG-UI is enabled via environment variable."""
        enabled_str = dotenv.get_dotenv_value("AGUI_ENABLED", str(AGUIConfig.DEFAULT_ENABLED))
        return enabled_str.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def get_transport() -> Literal["sse", "ws", "both"]:
        """Get transport configuration."""
        transport = dotenv.get_dotenv_value("AGUI_TRANSPORT", AGUIConfig.DEFAULT_TRANSPORT).lower()
        if transport not in ("sse", "ws", "both"):
            return AGUIConfig.DEFAULT_TRANSPORT
        return transport  # type: ignore

    @staticmethod
    def is_auth_required() -> bool:
        """Check if authentication is required."""
        auth_str = dotenv.get_dotenv_value("AGUI_AUTH_REQUIRED", str(AGUIConfig.DEFAULT_AUTH_REQUIRED))
        return auth_str.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def supports_sse() -> bool:
        """Check if SSE transport is enabled."""
        transport = AGUIConfig.get_transport()
        return transport in ("sse", "both")

    @staticmethod
    def supports_websocket() -> bool:
        """Check if WebSocket transport is enabled."""
        transport = AGUIConfig.get_transport()
        return transport in ("ws", "both")

