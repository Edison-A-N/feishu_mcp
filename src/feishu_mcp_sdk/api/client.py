"""Feishu API client for OAuth token management."""

from typing import Optional

from feishu_mcp_sdk.api.oauth_manager import OAuthManager
from feishu_mcp_sdk.config import settings


class FeishuClient:
    """
    Feishu API client for OAuth token management.

    This client handles user authorization via OAuth2 flow.
    It provides token management capabilities without relying on external SDKs.
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        oauth_manager: Optional[OAuthManager] = None,
    ):
        """
        Initialize Feishu client.

        Args:
            app_id: Feishu app ID (defaults to settings.app_id)
            app_secret: Feishu app secret (defaults to settings.app_secret)
            oauth_manager: Optional OAuth manager instance (creates new one if not provided)
        """
        app_id = app_id or settings.app_id
        app_secret = app_secret or settings.app_secret

        # Use composition pattern: integrate OAuthManager
        self._oauth_manager = oauth_manager or OAuthManager(
            app_id=app_id,
            app_secret=app_secret,
        )

    @property
    def oauth_manager(self) -> OAuthManager:
        """Get the OAuth manager instance."""
        return self._oauth_manager

    @property
    def user_token(self) -> Optional[str]:
        """Get the current user access token."""
        return self._oauth_manager.user_token

    async def ensure_user_token(self) -> str:
        """
        Ensure a valid user token is available, fetching one if necessary.

        Returns:
            Valid user access token

        Raises:
            ValueError: If no token is available and setup fails
        """
        return await self._oauth_manager.ensure_user_token()

    async def refresh_access_token(self) -> Optional[str]:
        """
        Refresh the user access token using refresh token.

        Returns:
            New access token, or None if refresh failed

        Note:
            If refresh fails, the stored tokens will be cleared to trigger re-authentication.
        """
        return await self._oauth_manager.refresh_access_token()

    def clear_tokens(self) -> None:
        """
        Clear stored tokens.

        This will force re-authentication on the next token request.
        """
        self._oauth_manager.clear_tokens()
