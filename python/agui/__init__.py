"""
AG-UI Integration Package

This package provides the AG-UI protocol integration for Argent,
allowing external UIs to connect and communicate with the agent.
"""

from python.agui.config import AGUIConfig
from python.agui.version import AGUI_VERSION, ADAPTER_VERSION

__all__ = ["AGUIConfig", "AGUI_VERSION", "ADAPTER_VERSION"]

