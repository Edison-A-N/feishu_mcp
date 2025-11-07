"""Feishu MCP SDK - A Model Context Protocol server for Feishu Document integration."""

from feishu_mcp_sdk.exceptions import ConfigurationError, FeishuMCPError
from feishu_mcp_sdk.server import create_app, run_server

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "create_app",
    "run_server",
    "FeishuMCPError",
    "ConfigurationError",
]
