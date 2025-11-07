"""HTTP client mixin for Feishu API services."""

from typing import Any, Dict, Optional

import httpx

from feishu_mcp_sdk.api.client import FeishuClient


class HTTPClientMixin:
    """
    Mixin class providing HTTP request capabilities for Feishu services.

    This mixin provides:
    - Token management
    - Automatic token refresh
    - Error handling
    - HTTP request methods (get, post, etc.)
    """

    def __init__(self, client: FeishuClient):
        """
        Initialize the mixin with a Feishu client.

        Args:
            client: Feishu client instance
        """
        self._client = client

    async def _ensure_token(self) -> str:
        """Ensure a valid user token is available."""
        return await self._client.ensure_user_token()

    async def _refresh_token_if_needed(self, response: httpx.Response) -> Optional[str]:
        """
        Refresh token if the response indicates token expiration.

        Args:
            response: HTTP response that may indicate token expiration

        Returns:
            New token if refreshed, None otherwise
        """
        if response.status_code == 401:
            return await self._client.refresh_access_token()
        return None

    async def _request(
        self, method: str, url: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> httpx.Response:
        """
        Make an HTTP request with automatic token management.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Optional headers dictionary
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response
        """
        user_token = await self._ensure_token()

        if headers is None:
            headers = {}

        headers["Authorization"] = f"Bearer {user_token}"
        headers.setdefault("Content-Type", "application/json")

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=headers, **kwargs)

            # Handle token refresh if needed
            if response.status_code == 401:
                new_token = await self._refresh_token_if_needed(response)
                if new_token:
                    # Refresh succeeded, retry with new token
                    headers["Authorization"] = f"Bearer {new_token}"
                    response = await client.request(method, url, headers=headers, **kwargs)
                else:
                    # Refresh failed, tokens have been cleared by refresh_access_token
                    # Force re-authentication by clearing tokens again (to be safe) and re-authenticating
                    self._client.clear_tokens()
                    # Force re-authentication - setup_user_token will complete the full OAuth flow
                    await self._client.oauth_manager.setup_user_token()
                    # Get the newly obtained token
                    new_token = self._client.user_token
                    if not new_token:
                        raise ValueError(
                            "Failed to obtain user access token after re-authentication"
                        )
                    headers["Authorization"] = f"Bearer {new_token}"
                    # Retry the original request with the new token
                    response = await client.request(method, url, headers=headers, **kwargs)

            if not response.is_success:
                print(response.text)

            return response

    async def _get(
        self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> httpx.Response:
        """
        Make a GET request.

        Args:
            url: Request URL
            headers: Optional headers dictionary
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response
        """
        return await self._request("GET", url, headers=headers, **kwargs)

    async def _post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Make a POST request.

        Args:
            url: Request URL
            json: Optional JSON data to send
            headers: Optional headers dictionary
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response
        """
        return await self._request("POST", url, json=json, headers=headers, **kwargs)

    async def _put(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Make a PUT request.

        Args:
            url: Request URL
            json: Optional JSON data to send
            headers: Optional headers dictionary
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response
        """
        return await self._request("PUT", url, json=json, headers=headers, **kwargs)

    async def _patch(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> httpx.Response:
        """
        Make a PATCH request.

        Args:
            url: Request URL
            json: Optional JSON data to send
            headers: Optional headers dictionary
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response
        """
        return await self._request("PATCH", url, json=json, headers=headers, **kwargs)

    async def _delete(
        self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> httpx.Response:
        """
        Make a DELETE request.

        Args:
            url: Request URL
            headers: Optional headers dictionary
            **kwargs: Additional arguments for httpx request

        Returns:
            HTTP response
        """
        return await self._request("DELETE", url, headers=headers, **kwargs)

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Parse API response and handle errors.

        Args:
            response: HTTP response

        Returns:
            Parsed response dictionary

        Raises:
            httpx.HTTPStatusError: If the response indicates an error
        """
        response.raise_for_status()
        result = response.json()

        if result.get("code") != 0:
            raise ValueError(f"API error: code={result.get('code')}, msg={result.get('msg')}")

        return result
