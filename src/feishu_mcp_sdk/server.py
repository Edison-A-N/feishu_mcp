"""MCP Server implementation for Feishu Document integration."""

from typing import Optional

from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP

from feishu_mcp_sdk.api.client import FeishuClient
from feishu_mcp_sdk.config import settings
from feishu_mcp_sdk.services.document_service import DocumentService

# Initialize FastMCP server
mcp = FastMCP(
    settings.mcp_server_name,
    port=settings.mcp_port,
    host="localhost",
    stateless_http=True,
)

# Initialize Feishu client
feishu_client = FeishuClient()

# Initialize document service
document_service = DocumentService(feishu_client)


@mcp.tool()
async def list_documents(
    folder_token: Optional[str] = None,
    page_size: int = 50,
    page_token: Optional[str] = None,
) -> dict:
    """
    List documents in a folder or root directory.

    Args:
        folder_token: Folder token (leave empty for root directory)
        page_size: Number of items per page (default: 50)
        page_token: Token for pagination (optional)

    Returns:
        Dictionary containing document list and pagination info
    """
    return await document_service.list_documents(
        folder_token=folder_token if folder_token else None,
        page_size=page_size,
        page_token=page_token if page_token else None,
    )


@mcp.tool()
async def get_document(
    document_id: str,
    include_raw_content: bool = False,
    lang: int = 0,
) -> dict:
    """
    Get document content by document ID.

    Args:
        document_id: Document token (can be extracted from Feishu document URL)
        include_raw_content: Whether to include raw text content (default: False)
        lang: Language for MentionUser (@user) display when getting raw content (default: 0)
            - 0: Default name (e.g., @John Doe)
            - 1: English name (e.g., @John Doe)
            - 2: Not supported, returns default name

    Returns:
        Dictionary containing document content and metadata.
        If include_raw_content is True, also includes raw_content field with plain text.

    Note:
        Rate limit: 5 requests per second per app. If exceeded, API returns HTTP 400
        with error code 99991400. Use exponential backoff or other rate limiting
        strategies when rate limited.
    """
    return await document_service.get_document_content(
        document_id=document_id,
        include_raw_content=include_raw_content,
        lang=lang,
    )


@mcp.tool()
async def get_document_blocks(
    document_id: str,
    page_size: int = 500,
    page_token: Optional[str] = None,
    document_revision_id: int = -1,
    user_id_type: str = "open_id",
) -> dict:
    """
    Get all blocks of a document with pagination.

    This API retrieves all blocks (content elements) of a Feishu document with support for
    pagination, version control, and user ID type configuration.

    **Rate Limit**: 5 requests per second per app. If exceeded, API returns HTTP 400
    with error code 99991400. Use exponential backoff or other rate limiting strategies
    when rate limited.

    Args:
        document_id: Document unique identifier (can be extracted from Feishu document URL)
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
            - items: List of block information with full details
            - page_token: Page token for next page (if has_more is true)
            - has_more: Whether there are more items
        - msg: Error message if failed

    Note:
        Each block in items contains detailed information including:
        - block_id: Block unique identifier
        - block_type: Block type (1=Page, 2=Text, 3-11=Heading1-9, etc.)
        - parent_id: Parent block ID
        - children: List of child block IDs
        - Various block-specific content (text, heading, code, etc.)
    """
    return await document_service.get_document_blocks(
        document_id=document_id,
        page_size=page_size,
        page_token=page_token if page_token else None,
        document_revision_id=document_revision_id,
        user_id_type=user_id_type,
    )


@mcp.tool()
async def get_document_info(document_id: str) -> dict:
    """
    Get document basic information (title and latest revision ID).

    Args:
        document_id: Document ID (can be extracted from Feishu document URL)

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
    return await document_service.get_document_info(document_id)


@mcp.tool()
async def search_documents(
    query: str,
    page_size: int = 50,
    page_token: Optional[str] = None,
) -> dict:
    """
    Search documents by query string.

    Args:
        query: Search query string
        page_size: Number of items per page (default: 50)
        page_token: Token for pagination (optional)

    Returns:
        Dictionary containing search results
    """
    return await document_service.search_documents(
        query=query,
        page_size=page_size,
        page_token=page_token if page_token else None,
    )


@mcp.tool()
async def update_document(
    document_id: str,
    content: str,
    block_id: Optional[str] = None,
) -> dict:
    """
    Update document content (append text to Docx document).

    Args:
        document_id: Document token (can be extracted from Feishu document URL)
        content: Text content to add to the document
        block_id: Optional block ID to insert after (leave empty to append to end)

    Returns:
        Dictionary containing update result
    """
    return await document_service.update_document(
        document_id=document_id,
        content=content,
        block_id=block_id if block_id else None,
    )


def create_app():
    """Create and configure the FastAPI app with CORS middleware."""
    app = mcp.sse_app()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

    return app


async def run_server(transport: str = "stdio"):
    """
    Run the MCP server with specified transport.

    Args:
        transport: Transport mode, either "stdio" or "streamable-http" (default: "stdio")
            - "stdio": Standard input/output transport
            - "streamable-http": Streamable HTTP transport
    """
    await mcp.run_async(transport=transport)
