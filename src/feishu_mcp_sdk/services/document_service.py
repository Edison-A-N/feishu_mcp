"""Document service for Feishu document management."""

from typing import Any, Dict, Optional

from feishu_mcp_sdk.api.client import FeishuClient
from feishu_mcp_sdk.services.http_client_mixin import HTTPClientMixin


class DocumentService(HTTPClientMixin):
    """
    Service for managing Feishu documents.

    Provides methods for:
    - Listing documents
    - Getting document content
    - Getting document blocks (with pagination)
    - Getting document basic information
    - Searching documents
    - Creating documents
    - Updating documents
    """

    def __init__(self, client: FeishuClient):
        """
        Initialize document service.

        Args:
            client: Feishu client instance
        """
        super().__init__(client)
        self._base_url = "https://open.feishu.cn/open-apis"

    async def list_documents(
        self,
        folder_token: Optional[str] = None,
        page_size: int = 50,
        page_token: Optional[str] = None,
    ) -> dict:
        """
        List documents using drive API.

        Args:
            folder_token: Folder token (leave empty for root directory)
            page_size: Number of items per page (default: 50)
            page_token: Token for pagination (optional)

        Returns:
            Dictionary containing document list and pagination info
        """
        try:
            uri = f"{self._base_url}/drive/v1/files"
            params: Dict[str, Any] = {"page_size": page_size}
            if folder_token:
                params["folder_token"] = folder_token
            if page_token:
                params["page_token"] = page_token

            response = await self._get(uri, params=params)
            result = self._parse_response(response)

            data = result.get("data", {})
            files_data = data.get("files", [])

            files = []
            for item in files_data:
                files.append(
                    {
                        "token": item.get("token"),
                        "name": item.get("name"),
                        "type": item.get("type"),
                        "parent_token": item.get("parent_token"),
                        "url": item.get("url"),
                    }
                )

            return {
                "success": True,
                "data": files,
                "page_token": data.get("page_token"),
                "has_more": data.get("has_more", False),
            }

        except Exception as e:
            return {
                "success": False,
                "msg": f"Failed to list documents: {str(e)}",
                "data": [],
            }

    async def get_document_content(
        self,
        document_id: str,
        include_raw_content: bool = False,
        lang: int = 0,
    ) -> dict:
        """
        Get document content by document ID.

        Args:
            document_id: Document ID (can be extracted from URL)
            include_raw_content: Whether to include raw text content (default: False)
            lang: Language for MentionUser (@user) display when getting raw content (default: 0)
                - 0: Default name (e.g., @John Doe)
                - 1: English name (e.g., @John Doe)
                - 2: Not supported, returns default name

        Returns:
            Dictionary containing document content and metadata
            If include_raw_content is True, also includes raw_content field with plain text

        Note:
            Rate limit: 5 requests per second per app. If exceeded, API returns HTTP 400
            with error code 99991400. Use exponential backoff or other rate limiting
            strategies when rate limited.
        """
        try:
            # Get document basic info
            uri = f"{self._base_url}/docx/v1/documents/{document_id}"
            response = await self._get(uri)
            result = self._parse_response(response)

            doc_data = result.get("data", {}).get("document", {})
            if not doc_data:
                return {
                    "success": False,
                    "msg": "Failed to get document content or document not found",
                }

            # Get raw content directly using raw_content API
            raw_uri = f"{self._base_url}/docx/v1/documents/{document_id}/raw_content"
            raw_params: Dict[str, Any] = {"lang": lang}
            raw_response = await self._get(raw_uri, params=raw_params)
            raw_result = self._parse_response(raw_response)
            raw_data = raw_result.get("data", {})
            raw_content = raw_data.get("content", "")

            result = {
                "success": True,
                "document_id": document_id,
                "title": doc_data.get("title"),
                "raw_content": raw_content,
            }

            return result

        except Exception as e:
            return {
                "success": False,
                "msg": f"Failed to get document content: {str(e)}",
            }

    async def get_document_blocks(
        self,
        document_id: str,
        page_size: int = 500,
        page_token: Optional[str] = None,
        document_revision_id: int = -1,
        user_id_type: str = "open_id",
    ) -> dict:
        """
        Get all blocks of a document with pagination.

        Reference: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/get

        Args:
            document_id: Document unique identifier
            page_size: Page size (default: 500, max: 500)
            page_token: Page token for pagination (optional). Leave empty for first request.
                If there are more items, a new page_token will be returned in the response.
            document_revision_id: Document version to query, -1 means latest version.
                Document version starts from 1.
                - To query latest version, requires document read permission
                - To query historical version, requires document edit permission
            user_id_type: User ID type (default: "open_id")
                - open_id: User identity in an app
                - union_id: User identity under an app developer
                - user_id: User identity within a tenant

        Returns:
            Dictionary containing:
            - success: Whether the request was successful
            - data: Dictionary containing:
                - items: List of block information
                - page_token: Page token for next page (if has_more is true)
                - has_more: Whether there are more items
            - msg: Error message if failed

        Note:
            Rate limit: 5 requests per second per app. If exceeded, API returns HTTP 400
            with error code 99991400. Use exponential backoff or other rate limiting
            strategies when rate limited.
        """
        try:
            uri = f"{self._base_url}/docx/v1/documents/{document_id}/blocks"

            params: Dict[str, Any] = {
                "page_size": min(page_size, 500),
                "document_revision_id": document_revision_id,
                "user_id_type": user_id_type,
            }

            if page_token:
                params["page_token"] = page_token

            response = await self._get(uri, params=params)
            result = self._parse_response(response)

            data = result.get("data", {})
            items = data.get("items", [])

            return {
                "success": True,
                "data": {
                    "items": items,
                    "page_token": data.get("page_token"),
                    "has_more": data.get("has_more", False),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "msg": f"Failed to get document blocks: {str(e)}",
                "data": {
                    "items": [],
                    "page_token": None,
                    "has_more": False,
                },
            }

    async def get_document_info(self, document_id: str) -> dict:
        """
        Get document basic information (title and latest revision ID).

        Reference: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/get

        Args:
            document_id: Document ID (can be extracted from URL)

        Returns:
            Dictionary containing document basic information:
            - document_id: Document unique identifier
            - revision_id: Document version ID (starts from 1)
            - title: Document title
            - display_setting: Document display settings
            - cover: Document cover information

        Note:
            Rate limit: 5 requests per second per app. If exceeded, API returns HTTP 400
            with error code 99991400. Use exponential backoff or other rate limiting
            strategies when rate limited.
        """
        try:
            uri = f"{self._base_url}/docx/v1/documents/{document_id}"
            response = await self._get(uri)
            result = self._parse_response(response)

            doc_data = result.get("data", {}).get("document", {})
            if not doc_data:
                return {
                    "success": False,
                    "msg": "Document not found or failed to get document information",
                }

            display_setting_data = doc_data.get("display_setting", {})
            display_setting = {
                "show_authors": display_setting_data.get("show_authors", False),
                "show_create_time": display_setting_data.get("show_create_time", False),
                "show_pv": display_setting_data.get("show_pv", False),
                "show_uv": display_setting_data.get("show_uv", False),
                "show_like_count": display_setting_data.get("show_like_count", False),
                "show_comment_count": display_setting_data.get("show_comment_count", False),
                "show_related_matters": display_setting_data.get("show_related_matters", False),
            }

            cover_data = doc_data.get("cover", {})
            cover = None
            if cover_data:
                cover = {
                    "token": cover_data.get("token"),
                    "offset_ratio_x": cover_data.get("offset_ratio_x", 0.0),
                    "offset_ratio_y": cover_data.get("offset_ratio_y", 0.0),
                }

            return {
                "success": True,
                "document_id": doc_data.get("document_id"),
                "revision_id": doc_data.get("revision_id"),
                "title": doc_data.get("title"),
                "display_setting": display_setting,
                "cover": cover,
            }

        except Exception as e:
            return {
                "success": False,
                "msg": f"Failed to get document information: {str(e)}",
            }

    def _extract_block_text(self, block: Dict[str, Any]) -> str:
        """
        Extract text content from a document block.

        Args:
            block: Block data dictionary

        Returns:
            Extracted text content
        """
        try:
            text_data = block.get("text", {})
            if not text_data:
                return ""

            elements = text_data.get("elements", [])
            texts = []
            for elem in elements:
                text_run = elem.get("text_run", {})
                if text_run:
                    texts.append(text_run.get("content", ""))
                elif "text" in elem:
                    texts.append(elem.get("text", ""))

            return "".join(texts)
        except Exception:
            return ""

    async def search_documents(
        self,
        query: str,
        page_size: int = 20,
        page_token: Optional[str] = None,
        owner_ids: Optional[list] = None,
        chat_ids: Optional[list] = None,
        docs_types: Optional[list] = None,
    ) -> dict:
        """
        Search documents using suite/docs-api/search/object API.

        Reference: https://open.feishu.cn/document/server-docs/docs/drive-v1/search/document-search

        Args:
            query: Search query string (required, maps to search_key)
            page_size: Number of items per page (default: 20, maps to count, max 50)
            page_token: Offset for pagination (optional, maps to offset, must be int)
            owner_ids: File owner Open IDs (optional)
            chat_ids: Chat IDs where files are located (optional)
            docs_types: File types to filter (optional, e.g., ["doc", "sheet"])

        Returns:
            Dictionary containing search results with docs_entities, has_more, total
        """
        try:
            uri = f"{self._base_url}/suite/docs-api/search/object"

            params: Dict[str, Any] = {
                "search_key": query,
                "count": min(page_size, 50),
            }

            if page_token:
                try:
                    params["offset"] = int(page_token)
                except (ValueError, TypeError):
                    params["offset"] = 0
            else:
                params["offset"] = 0

            if owner_ids:
                params["owner_ids"] = owner_ids
            if chat_ids:
                params["chat_ids"] = chat_ids
            if docs_types:
                params["docs_types"] = docs_types

            response = await self._post(uri, json=params)
            result = self._parse_response(response)

            data = result.get("data", {})
            docs_entities = data.get("docs_entities", [])

            files = []
            for item in docs_entities:
                files.append(
                    {
                        "token": item.get("docs_token"),
                        "name": item.get("title"),
                        "title": item.get("title"),
                        "type": item.get("docs_type"),
                        "owner_id": item.get("owner_id"),
                    }
                )

            return {
                "success": True,
                "data": files,
                "has_more": data.get("has_more", False),
                "total": data.get("total", 0),
            }

        except Exception as e:
            return {
                "success": False,
                "msg": f"Failed to search documents: {str(e)}",
                "data": [],
            }

    async def update_document(
        self,
        document_id: str,
        content: Optional[str] = None,
        block_id: Optional[str] = None,
        requests: Optional[list] = None,
        document_revision_id: int = -1,
        client_token: Optional[str] = None,
        user_id_type: str = "open_id",
    ) -> dict:
        """
        Update document content using batch_update API.

        Reference: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/batch_update

        Args:
            document_id: Document token
            content: (Simple mode) Text content to update
            block_id: (Simple mode) Block ID to update
            requests: (Advanced mode) List of update_block_request objects
            document_revision_id: Document version (-1 for latest, default: -1)
            client_token: Client token for idempotency (optional)
            user_id_type: User ID type (default: "open_id")

        Returns:
            Dictionary containing update result
        """
        try:
            # Determine which mode to use
            if requests is not None:
                # Advanced mode: use provided requests
                update_requests = requests
            elif content is not None and block_id is not None:
                # Simple mode: construct request from content and block_id
                if not block_id:
                    return {
                        "success": False,
                        "msg": "block_id is required for updating document blocks",
                    }
                update_requests = [
                    {
                        "block_id": block_id,
                        "update_text_elements": {
                            "elements": [
                                {
                                    "text_run": {
                                        "content": content,
                                    },
                                },
                            ],
                        },
                    },
                ]
            else:
                return {
                    "success": False,
                    "msg": "Either (content and block_id) or requests must be provided",
                }

            uri = f"{self._base_url}/docx/v1/documents/{document_id}/blocks/batch_update"
            params: Dict[str, Any] = {
                "requests": update_requests,
            }

            # Build query parameters
            query_params: Dict[str, Any] = {
                "document_revision_id": document_revision_id,
                "user_id_type": user_id_type,
            }
            if client_token:
                query_params["client_token"] = client_token

            # Build URL with query parameters
            if query_params:
                from urllib.parse import urlencode

                query_string = urlencode(query_params)
                uri = f"{uri}?{query_string}"

            response = await self._patch(uri, json=params)
            result = self._parse_response(response)

            data = result.get("data", {})
            responses = data.get("responses", [])

            # Return full response for advanced mode, simplified for simple mode
            if requests is not None:
                # Advanced mode: return full response
                return {
                    "success": True,
                    "message": "Document updated successfully",
                    "data": data,
                }
            else:
                # Simple mode: return simplified response
                if responses:
                    update_result = responses[0]
                    return {
                        "success": True,
                        "message": "Document updated successfully",
                        "block_id": update_result.get("block_id"),
                        "status": update_result.get("status"),
                    }
                else:
                    return {
                        "success": False,
                        "msg": "No response from batch update",
                    }

        except Exception as e:
            return {
                "success": False,
                "msg": f"Failed to update document: {str(e)}",
            }

    async def create_blocks(
        self,
        document_id: str,
        block_id: str,
        children: list,
        index: int = -1,
        document_revision_id: int = -1,
        client_token: Optional[str] = None,
        user_id_type: str = "open_id",
    ) -> dict:
        """
        Create blocks in a document.

        Reference: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block-children/create

        Args:
            document_id: Document token
            block_id: Parent block ID (use document_id for root level)
            children: List of block objects to create
            index: Index to insert blocks at (default: -1, inserts at end).
                Index starts from 0 (first position). Use -1 to insert at the last position.
            document_revision_id: Document version (-1 for latest, default: -1)
            client_token: Client token for idempotency (optional)
            user_id_type: User ID type (default: "open_id")

        Returns:
            Dictionary containing created blocks information
        """
        try:
            uri = f"{self._base_url}/docx/v1/documents/{document_id}/blocks/{block_id}/children"
            params: Dict[str, Any] = {
                "index": index,
                "children": children,
            }

            query_params: Dict[str, Any] = {
                "document_revision_id": document_revision_id,
                "user_id_type": user_id_type,
            }
            if client_token:
                query_params["client_token"] = client_token

            # Build URL with query parameters
            if query_params:
                from urllib.parse import urlencode

                query_string = urlencode(query_params)
                uri = f"{uri}?{query_string}"

            response = await self._post(uri, json=params)
            result = self._parse_response(response)

            data = result.get("data", {})
            created_blocks = data.get("children", [])
            return {
                "success": True,
                "message": "Blocks created successfully",
                "children": created_blocks,
            }

        except Exception as e:
            return {
                "success": False,
                "msg": f"Failed to create blocks: {str(e)}",
            }

    async def delete_blocks(
        self,
        document_id: str,
        block_id: str,
        start_index: int,
        end_index: int,
        document_revision_id: int = -1,
        client_token: Optional[str] = None,
    ) -> dict:
        """
        Delete blocks from a document.

        Reference: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block-children/batch_delete

        Args:
            document_id: Document unique identifier
            block_id: Parent block ID (use document_id for root level)
            start_index: Starting index for deletion (inclusive, left-closed interval)
            end_index: Ending index for deletion (exclusive, right-open interval)
                start_index must be less than end_index
            document_revision_id: Document version to operate on (-1 for latest, default: -1)
            client_token: Client token for idempotency (optional)

        Returns:
            Dictionary containing:
            - success: Boolean indicating if operation succeeded
            - message: Status message
            - document_revision_id: Document version after deletion
            - client_token: Client token for idempotency

        Note:
            Application rate limit: 3 requests per second per app. If exceeded, API returns HTTP 400
            with error code 99991400. Use exponential backoff or other rate limiting strategies.

            Document rate limit: 3 concurrent edits per second per document (includes create,
            update, delete operations). If exceeded, API returns HTTP 429.

            Important restrictions:
            - Cannot delete table rows/columns or grid columns (use update_block API instead)
            - Cannot delete all children of TableCell, GridColumn, or Callout blocks
        """
        try:
            uri = f"{self._base_url}/docx/v1/documents/{document_id}/blocks/{block_id}/children/batch_delete"

            # Build query parameters
            query_params: Dict[str, Any] = {
                "document_revision_id": document_revision_id,
            }
            if client_token:
                query_params["client_token"] = client_token

            # Build URL with query parameters
            if query_params:
                from urllib.parse import urlencode

                query_string = urlencode(query_params)
                uri = f"{uri}?{query_string}"

            # Build request body
            body: Dict[str, Any] = {
                "start_index": start_index,
                "end_index": end_index,
            }

            response = await self._delete(uri, json=body)
            result = self._parse_response(response)

            data = result.get("data", {})
            return {
                "success": True,
                "message": "Blocks deleted successfully",
                "document_revision_id": data.get("document_revision_id"),
                "client_token": data.get("client_token"),
            }

        except Exception as e:
            return {
                "success": False,
                "msg": f"Failed to delete blocks: {str(e)}",
            }
