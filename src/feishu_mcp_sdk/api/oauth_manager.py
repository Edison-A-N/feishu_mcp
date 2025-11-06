"""OAuth manager for Feishu user authorization."""

import asyncio
import json
import logging
import socket
import webbrowser
from pathlib import Path
from typing import Optional

import httpx
from aiohttp import web

from feishu_mcp_sdk.config import settings

logger = logging.getLogger(__name__)


class OAuthManager:
    """
    Manages OAuth2 user authorization flow for Feishu.

    This class handles:
    - OAuth2 authorization code flow
    - Access token acquisition and storage
    - Token refresh
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        oauth_redirect_uri: Optional[str] = None,
        oauth_callback_port: Optional[int] = None,
        oauth_scope: Optional[str] = None,
        oauth_authorize_url: Optional[str] = None,
        oauth_token_url: Optional[str] = None,
        oauth_callback_url: Optional[str] = None,
    ):
        """
        Initialize OAuth manager.

        Args:
            app_id: Feishu app ID (defaults to settings.app_id)
            app_secret: Feishu app secret (defaults to settings.app_secret)
            oauth_redirect_uri: OAuth redirect URI (defaults to settings.redirect_uri)
            oauth_callback_port: OAuth callback port (defaults to settings.oauth_callback_port)
            oauth_scope: OAuth scope (defaults to settings.oauth_scope)
            oauth_authorize_url: OAuth authorize URL (defaults to settings.oauth_authorize_url)
            oauth_token_url: OAuth token URL (defaults to settings.oauth_token_url)
            oauth_callback_url: OAuth callback URL (unused, kept for compatibility)
        """
        self.app_id = app_id or settings.app_id
        self.app_secret = app_secret or settings.app_secret
        self.oauth_redirect_uri = oauth_redirect_uri or settings.oauth_redirect_uri
        self.oauth_callback_port = oauth_callback_port or settings.oauth_callback_port
        self.oauth_scope = oauth_scope or settings.oauth_scope
        self.oauth_authorize_url = oauth_authorize_url or settings.oauth_authorize_url
        self.oauth_token_url = oauth_token_url or settings.oauth_token_url
        self._user_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

        # Setup cache directory
        self._cache_dir = Path.home() / ".feishu_mcp"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self._cache_dir / "tokens.json"

        # Load tokens from cache on initialization
        self._load_tokens_from_cache()

    @property
    def user_token(self) -> Optional[str]:
        """Get the current user access token."""
        return self._user_token

    @property
    def refresh_token(self) -> Optional[str]:
        """Get the current refresh token."""
        return self._refresh_token

    def _load_tokens_from_cache(self) -> None:
        """Load tokens from cache file."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Only load if app_id matches (to avoid using wrong app's tokens)
                    if data.get("app_id") == self.app_id:
                        self._user_token = data.get("access_token")
                        self._refresh_token = data.get("refresh_token")
        except Exception as e:
            # If loading fails, just continue without cached tokens
            logger.debug(f"Failed to load tokens from cache: {e}")

    def _save_tokens_to_cache(self) -> None:
        """Save tokens to cache file."""
        try:
            data = {
                "app_id": self.app_id,
                "access_token": self._user_token,
                "refresh_token": self._refresh_token,
            }
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            # If saving fails, just continue without caching
            logger.debug(f"Failed to save tokens to cache: {e}")

    def set_tokens(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """
        Set the user access token and refresh token.

        Args:
            access_token: User access token
            refresh_token: Optional refresh token
        """
        self._user_token = access_token
        if refresh_token:
            self._refresh_token = refresh_token
        # Save to cache whenever tokens are set
        self._save_tokens_to_cache()

    def clear_tokens(self) -> None:
        """Clear stored tokens."""
        self._user_token = None
        self._refresh_token = None
        # Remove cache file
        try:
            if self._cache_file.exists():
                self._cache_file.unlink()
        except Exception as e:
            logger.debug(f"Failed to remove cache file: {e}")

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return False
            except OSError:
                return True

    async def _wait_for_port_release(
        self, port: int, max_wait: float = 5.0, check_interval: float = 0.1
    ) -> bool:
        """
        Wait for a port to be released.

        Args:
            port: Port to check
            max_wait: Maximum time to wait in seconds
            check_interval: Interval between checks in seconds

        Returns:
            True if port is released, False if timeout
        """
        elapsed = 0.0
        while elapsed < max_wait:
            if not self._is_port_in_use(port):
                return True
            await asyncio.sleep(check_interval)
            elapsed += check_interval
        return False

    async def get_code(self, timeout: int = 300) -> str:
        """
        Get OAuth2 authorization code via browser flow.

        Args:
            timeout: Maximum time to wait for authorization in seconds (default: 300)

        Returns:
            Authorization code

        Raises:
            ValueError: If authorization fails
            asyncio.TimeoutError: If authorization times out
        """
        # Check if port is in use and wait for release if needed
        if self._is_port_in_use(self.oauth_callback_port):
            # Wait a bit for the port to be released (previous instance might be closing)
            if not await self._wait_for_port_release(self.oauth_callback_port):
                raise OSError(
                    f"Port {self.oauth_callback_port} is already in use. "
                    f"Please ensure no other instance is running or wait for it to release the port. "
                    f"If the problem persists, you may need to restart your system or kill the process using the port."
                )

        # Create a Future to store the authorization code
        code_future = asyncio.Future()

        # Create a callback handler
        async def handle_callback(request):
            code = request.query.get("code")
            if code:
                if not code_future.done():
                    code_future.set_result(code)
                return web.Response(
                    text="""
                    <script>
                        setTimeout(function() {
                            window.close();
                        }, 1000);
                    </script>
                    Authorization successful! The page will close automatically...
                    """,
                    content_type="text/html",
                )
            if not code_future.done():
                code_future.set_exception(ValueError("Authorization failed: no code received"))
            return web.Response(text="Authorization failed!")

        # Setup local server
        app = web.Application()
        app.router.add_get("/oauth/callback", handle_callback)
        runner = web.AppRunner(app)
        site = None

        try:
            await runner.setup()
            site = web.TCPSite(runner, "localhost", self.oauth_callback_port)
            await site.start()

            # Open browser for authorization
            auth_url = (
                f"{self.oauth_authorize_url}"
                f"?client_id={self.app_id}"
                f"&redirect_uri=http://localhost:{self.oauth_callback_port}{self.oauth_redirect_uri}"
                "&response_type=code"
            )
            if self.oauth_scope:
                auth_url += f"&scope={self.oauth_scope}"
            logger.info(auth_url)
            logger.info(f"\nWaiting for authorization on port {self.oauth_callback_port}...")
            logger.info("Press Ctrl+C to cancel if you closed the browser page.\n")
            webbrowser.open(auth_url)

            # Wait for the callback with timeout
            try:
                code = await asyncio.wait_for(code_future, timeout=timeout)
                return code
            except asyncio.TimeoutError:
                # If timeout, ensure we clean up and provide helpful message
                if not code_future.done():
                    code_future.cancel()
                raise asyncio.TimeoutError(
                    f"Authorization timed out after {timeout} seconds. "
                    f"If you closed the browser page, the server has been cleaned up."
                )
            except asyncio.CancelledError:
                # If cancelled (e.g., Ctrl+C), ensure cleanup and provide helpful message
                if not code_future.done():
                    code_future.cancel()
                raise
        except KeyboardInterrupt:
            # Handle user cancellation (Ctrl+C)
            if not code_future.done():
                code_future.cancel()
            raise KeyboardInterrupt("Authorization cancelled by user. Server has been cleaned up.")
        except Exception:
            # Any other exception, ensure cleanup
            if not code_future.done():
                code_future.cancel()
            raise
        finally:
            # Ensure proper cleanup: stop site first, then cleanup runner
            # This ensures port is always released, even if page was closed
            try:
                if site is not None:
                    await site.stop()
            except Exception:
                pass  # Ignore errors during cleanup
            try:
                await runner.cleanup()
            except Exception:
                pass  # Ignore errors during cleanup
            # Give the OS a moment to release the port
            await asyncio.sleep(0.1)

    async def get_access_token(self, code: str) -> tuple[str, Optional[str]]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Tuple of (access_token, refresh_token)

        Raises:
            httpx.HTTPStatusError: If token exchange fails
        """
        url = self.oauth_token_url

        data = {
            "grant_type": "authorization_code",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "code": code,
            "redirect_uri": f"http://localhost:{self.oauth_callback_port}{self.oauth_redirect_uri}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            results = response.json()

        access_token = results.get("access_token")
        refresh_token = results.get("refresh_token")
        return access_token, refresh_token

    async def refresh_access_token(self) -> Optional[str]:
        """
        Refresh the user access token using refresh token.

        Returns:
            New access token, or None if refresh failed

        Note:
            If refresh fails, the stored tokens will be cleared to trigger re-authentication.
        """
        if not self._refresh_token:
            return None

        url = self.oauth_token_url

        data = {
            "grant_type": "refresh_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "refresh_token": self._refresh_token,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                results = response.json()

            access_token = results.get("access_token")
            refresh_token = results.get("refresh_token")
            if access_token:
                self.set_tokens(access_token, refresh_token)
            return access_token
        except httpx.HTTPStatusError as e:
            # If refresh fails (e.g., 401), clear tokens to trigger re-authentication
            if e.response.status_code == 401:
                self.clear_tokens()
            return None
        except Exception:
            # Clear tokens on any refresh failure to trigger re-authentication
            self.clear_tokens()
            return None

    async def setup_user_token(self) -> None:
        """
        Setup user access token by completing the OAuth2 authorization flow.

        Raises:
            ValueError: If authorization or token exchange fails
        """
        code = await self.get_code()
        access_token, refresh_token = await self.get_access_token(code)
        if not access_token:
            raise ValueError("Failed to obtain access token")
        self.set_tokens(access_token, refresh_token)

    async def ensure_user_token(self) -> str:
        """
        Ensure a valid user token is available, fetching one if necessary.

        Returns:
            Valid user access token

        Raises:
            ValueError: If no token is available and setup fails
        """
        if self._user_token:
            return self._user_token

        # Auto-authenticate
        await self.setup_user_token()
        if not self._user_token:
            raise ValueError("Failed to obtain user access token")
        return self._user_token
