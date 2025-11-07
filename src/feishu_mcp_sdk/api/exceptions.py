"""Custom exceptions for Feishu API errors."""

from feishu_mcp_sdk.exceptions import FeishuMCPError


class FeishuError(FeishuMCPError):
    """Base exception for all Feishu API errors."""

    def __init__(self, message: str, code: int = None, details: dict = None):
        """
        Initialize Feishu error.

        Args:
            message: Error message
            code: Error code from Feishu API (if available)
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class FeishuAPIError(FeishuError):
    """Exception raised when Feishu API returns an error response."""

    def __init__(self, message: str, code: int, details: dict = None):
        """
        Initialize Feishu API error.

        Args:
            message: Error message from API
            code: Error code from Feishu API
            details: Additional error details from API response
        """
        super().__init__(message, code, details)
        self.code = code

    def __str__(self) -> str:
        """Return formatted error string."""
        if self.code:
            return f"Feishu API Error [{self.code}]: {self.message}"
        return f"Feishu API Error: {self.message}"


class FeishuRateLimitError(FeishuAPIError):
    """Exception raised when rate limit is exceeded (429 or specific error codes)."""

    def __init__(self, message: str = "Rate limit exceeded", code: int = 429, details: dict = None):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            code: Error code (default: 429)
            details: Additional error details
        """
        super().__init__(message, code, details)

    def __str__(self) -> str:
        """Return formatted error string."""
        return f"Feishu Rate Limit Error: {self.message}"


class FeishuAuthenticationError(FeishuAPIError):
    """Exception raised when authentication fails."""

    def __init__(
        self, message: str = "Authentication failed", code: int = None, details: dict = None
    ):
        """
        Initialize authentication error.

        Args:
            message: Error message
            code: Error code (typically 99991677 or 99991668 for token issues)
            details: Additional error details
        """
        super().__init__(message, code, details)

    def __str__(self) -> str:
        """Return formatted error string."""
        return f"Feishu Authentication Error [{self.code}]: {self.message}"


class FeishuNetworkError(FeishuError):
    """Exception raised when network errors occur."""

    def __init__(self, message: str, original_error: Exception = None):
        """
        Initialize network error.

        Args:
            message: Error message
            original_error: Original exception that caused the error
        """
        super().__init__(message)
        self.original_error = original_error

    def __str__(self) -> str:
        """Return formatted error string."""
        if self.original_error:
            return f"Feishu Network Error: {self.message} (Original: {type(self.original_error).__name__})"
        return f"Feishu Network Error: {self.message}"


class FeishuRequestError(FeishuError):
    """Exception raised when HTTP request fails."""

    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        """
        Initialize request error.

        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Response body (if available)
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        """Return formatted error string."""
        if self.status_code:
            return f"Feishu Request Error [{self.status_code}]: {self.message}"
        return f"Feishu Request Error: {self.message}"
