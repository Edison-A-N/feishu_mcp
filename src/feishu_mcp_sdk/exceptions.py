"""Base exceptions for Feishu MCP SDK."""


class FeishuMCPError(Exception):
    """Base exception for all Feishu MCP SDK errors."""

    def __init__(self, message: str):
        """
        Initialize Feishu MCP error.

        Args:
            message: Error message
        """
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        """Return formatted error string."""
        return f"Feishu MCP Error: {self.message}"


class ConfigurationError(FeishuMCPError):
    """Exception raised when required configuration is missing or invalid."""

    def __init__(self, message: str):
        """
        Initialize configuration error.

        Args:
            message: Error message describing the configuration issue
        """
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        """Return formatted error string."""
        return f"Configuration Error: {self.message}"
