"""MCP Server implementation for Feishu Document integration."""

from pathlib import Path
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


@mcp.resource("docx://block-structure", mime_type="text/markdown")
async def get_block_structure() -> str:
    """
    Get comprehensive DocX block data structure documentation.

    This resource provides detailed information about all block types, their data structures,
    content entities, and enumerations used in Feishu DocX documents. It includes:
    - Block type definitions and block_type enum values
    - Content entity structures (BlockData) for each block type
    - Text element structures (TextElement, TextRun, MentionUser, MentionDoc, etc.)
    - Style structures (TextStyle, TextElementStyle)
    - All enumeration values (Align, FontColor, CodeLanguage, etc.)

    Use this resource when you need to understand the exact data structure for:
    - Creating blocks with complex content (links, images, mentions, etc.)
    - Updating blocks with specific formatting or embedded content
    - Understanding enum values for alignment, colors, languages, etc.

    Returns:
        Markdown-formatted documentation (text/markdown) containing complete block structure specifications
    """
    # Get the path to docx_block_structure.md file in resources directory
    current_dir = Path(__file__).parent
    doc_path = current_dir / "resources" / "docx_block_structure.md"

    if doc_path.exists():
        return doc_path.read_text(encoding="utf-8")
    else:
        # Fallback: return a message if file not found
        return "# DocX Block Structure Documentation\n\nDocumentation file not found. Please ensure docx_block_structure.md exists in the resources directory."


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
    content: Optional[str] = None,
    block_id: Optional[str] = None,
    requests: Optional[list] = None,
    document_revision_id: int = -1,
    client_token: Optional[str] = None,
    user_id_type: str = "open_id",
) -> dict:
    """
    Update document content using batch_update API.

    This tool supports two usage modes:
    1. Simple mode: Update text content by providing content and block_id
    2. Advanced mode: Provide full requests list to support all batch_update capabilities

    **Important**: For complex data structures involving hyperlinks, image embeds, mentions (@user, @doc),
    text formatting, or other advanced block features, refer to the block structure resource
    `docx://block-structure` to understand the exact data structure requirements before making updates.

    Args:
        document_id: Document unique identifier (can be extracted from Feishu document URL).
            Example: "doxcnePuYufKa49ISjhD8Iabcef"
        content: (Simple mode) Text content to update. To implement line breaks:
            - Add `\\n` for soft break (Shift + Enter), may be ignored by renderer
            - Create a new text Block for hard break (Enter), always displayed as new line
            Maximum length: 100,000 UTF-16 encoded characters per text block
        block_id: (Simple mode) Block ID to update. Required when using simple mode.
            You can get block_id by calling get_document_blocks API.
        requests: (Advanced mode) List of update_block_request objects. Each request must have:
            - block_id (required): Block ID to update
            - One of the following update operations (all optional):
                * update_text_elements: Update text elements (text_run, mention_user, mention_doc, reminder, etc.)
                * update_text_style: Update text style (align, done, folded, language, wrap, background_color, etc.)
                * update_table_property: Update table properties (column_width, header_row, header_column)
                * insert_table_row: Insert table row (row_index: -1 for end)
                * insert_table_column: Insert table column (column_index: -1 for end)
                * delete_table_rows: Delete table rows (row_start_index, row_end_index)
                * delete_table_columns: Delete table columns (column_start_index, column_end_index)
                * merge_table_cells: Merge table cells (row_start_index, row_end_index, column_start_index, column_end_index)
                * unmerge_table_cells: Unmerge table cells (row_index, column_index)
                * insert_grid_column: Insert grid column (column_index: 1-based, -1 for end)
                * delete_grid_column: Delete grid column (column_index: 0-based, -1 for last)
                * update_grid_column_width_ratio: Update grid column width ratio (width_ratios: list of percentages)
                * replace_image: Replace image (token, width, height, align, caption)
                * replace_file: Replace file attachment (token, block_id)
                * update_text: Update text elements and style (elements: list of text_element)
                * update_task: Update task block (task_id, folded)

            For detailed structure of text elements (links, mentions, formatting), refer to resource: docx://block-structure
        document_revision_id: Document version to operate on. -1 means latest version.
            Document version starts from 1. To query latest version, requires document read permission.
            To query historical version, requires document edit permission.
        client_token: Client token for idempotency (optional). If provided, the operation will be
            idempotent. Leave empty to initiate a new request.
        user_id_type: User ID type (default: "open_id")
            - open_id: User identity in an app
            - union_id: User identity under an app developer
            - user_id: User identity within a tenant

    Simple Mode Example:
        update_document(
            document_id="doxcnePuYufKa49ISjhD8Iabcef",
            content="Updated text content",
            block_id="doxcnk0i44OMOaouw8AdXuXrp6b"
        )

    Advanced Mode Example:
        update_document(
            document_id="doxcnePuYufKa49ISjhD8Iabcef",
            requests=[
                {
                    "block_id": "doxcnk0i44OMOaouw8AdXuXrp6b",
                    "update_text_style": {
                        "style": {
                            "align": 2,  # Center align
                            "fields": [1]  # Update alignment
                        }
                    }
                },
                {
                    "block_id": "doxcn0K8iGSMW4Mqgs9qlyTP50d",
                    "update_text_elements": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": "Hello",
                                    "text_element_style": {
                                        "bold": True,
                                        "text_color": 5  # Blue
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        )

    Supported Block Types for Text Updates:
        - Page (block_type=1)
        - Text (block_type=2)
        - Heading1-9 (block_type=3-11)
        - Bullet (block_type=12)
        - Ordered (block_type=13)
        - Code (block_type=14)
        - Quote (block_type=15)
        - Todo (block_type=17)

    Important Constraints:
        - Maximum 200 requests per batch update
        - Cannot update the same block multiple times in a single batch update
        - Block IDs in requests must be unique within the batch
        - When using simple mode, both content and block_id are required
        - When using advanced mode, requests parameter is required

    Returns:
        Dictionary containing:
        - success: Boolean indicating if operation succeeded
        - message: Status message
        - data: Response data from batch_update API (if advanced mode)
        - block_id: Updated block ID (if simple mode)
        - status: Update status

    Note:
        Application rate limit: 3 requests per second per app. If exceeded, API returns HTTP 400
        with error code 99991400. Use exponential backoff or other rate limiting strategies.

        Document rate limit: 3 concurrent edits per second per document (includes create,
        update, delete operations). If exceeded, API returns HTTP 429.
    """
    return await document_service.update_document(
        document_id=document_id,
        content=content,
        block_id=block_id if block_id else None,
        requests=requests,
        document_revision_id=document_revision_id,
        client_token=client_token if client_token else None,
        user_id_type=user_id_type,
    )


@mcp.tool()
async def create_blocks(
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

    **Important**: For complex block structures involving hyperlinks, image embeds, mentions (@user, @doc),
    text formatting, tables, or other advanced features, refer to the block structure resource
    `docx://block-structure` to understand the exact data structure requirements before creating blocks.

    Args:
        document_id: Document token (can be extracted from Feishu document URL)
        block_id: Parent block ID (use document_id for root level). Valid parent blocks include:
            - Page (block_id = document_id)
            - Text, Heading1-9, Bullet, Ordered, Todo, Task blocks
            - TableCell, GridColumn, Callout, QuoteContainer blocks
        children: List of block objects to create. Each block must have:
            - block_type (int): Block type number (see Block Types below)
            - Content fields based on block_type (see Block Structure below)

            For detailed structure of all block types and their content entities, refer to resource: docx://block-structure
        index: Index to insert blocks at (default: -1, inserts at end).
            Index starts from 0 (first position). Use -1 to insert at the last position.
        document_revision_id: Document version (-1 for latest, default: -1)
        client_token: Client token for idempotency (optional)
        user_id_type: User ID type - "open_id", "union_id", or "user_id" (default: "open_id")

    Block Types (block_type values):
        Text blocks: 2=Text, 3-11=Heading1-9, 12=Bullet, 13=Ordered, 14=Code, 15=Quote, 17=Todo
        Visual blocks: 22=Divider (empty object {}), 27=Image, 23=File, 26=Iframe
        Data blocks: 18=Bitable, 30=Sheet, 29=Mindnote (not supported)
        Container blocks: 24=Grid, 25=GridColumn (cannot be created directly), 19=Callout
        Table blocks: 31=Table, 32=TableCell (cannot be created directly)
        Other: 20=ChatCard, 28=ISV, 34=QuoteContainer, 35=Task (not supported), 36=OKR
        Special: 1=Page (auto-created, cannot be created), 999=Undefined (invalid)

    Block Structure Examples:
        Text block (block_type=2):
            {
                "block_type": 2,
                "text": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "Your text here",
                                "text_element_style": {
                                    "bold": true,
                                    "text_color": 5
                                }
                            }
                        }
                    ]
                }
            }

        Heading block (block_type=3 for H1):
            {
                "block_type": 3,
                "heading1": {
                    "elements": [{"text_run": {"content": "Heading text"}}]
                }
            }

        Divider block (block_type=22):
            {"block_type": 22}

    Parent-Child Rules:
        Valid parent blocks: Page, Text, Heading1-9, Bullet, Ordered, Todo, Task, TableCell,
        GridColumn, Callout, QuoteContainer

        Invalid child blocks (cannot be created as children):
        - Page (auto-created, only one per document)
        - GridColumn (use InsertGridColumnRequest in update_block)
        - TableCell (use InsertTableRowRequest/InsertTableColumnRequest in update_block)
        - View (auto-created with File blocks)
        - Mindnote, Diagram (not supported)
        - Undefined (invalid)

        Special restrictions:
        - TableCell: Cannot contain Table, Sheet, Bitable, OKR as children
        - GridColumn: Cannot contain Grid, Bitable, OKR as children
        - Callout: Can only contain Text, Heading, Ordered, Bullet, Task, Todo, Quote, QuoteContainer

    Supported Block Operations:
        Create: Callout, Table, Text, Divider, Grid, Iframe, ChatCard, Image, File, ISV,
        Bitable, Sheet, QuoteContainer, OKR, AddOns, WikiCatalog, Board, LinkPreview, SubPageList
        Not supported: Mindnote, Diagram, Task, Agenda, SourceSynced, ReferenceSynced, AITemplate

    Returns:
        Dictionary containing:
        - success: Boolean indicating if operation succeeded
        - message: Status message
        - children: List of created block objects with block_id, parent_id, block_type, etc.

    Note:
        Rate limit: 3 requests per second per app. If exceeded, API returns HTTP 400
        with error code 99991400. Use exponential backoff or other rate limiting
        strategies when rate limited.

        Document rate limit: 3 concurrent edits per second per document (includes create,
        update, delete operations). If exceeded, API returns HTTP 429.
    """
    return await document_service.create_blocks(
        document_id=document_id,
        block_id=block_id,
        children=children,
        index=index,
        document_revision_id=document_revision_id,
        client_token=client_token if client_token else None,
        user_id_type=user_id_type,
    )


@mcp.tool()
async def delete_blocks(
    document_id: str,
    block_id: str,
    start_index: int,
    end_index: int,
    document_revision_id: int = -1,
    client_token: Optional[str] = None,
) -> dict:
    """
    Delete blocks from a document.

    This tool deletes a range of child blocks from a specified parent block in a Feishu document.
    The deletion uses a left-closed, right-open interval [start_index, end_index).

    **Rate Limits**:
    - Application rate limit: 3 requests per second per app. If exceeded, API returns HTTP 400
      with error code 99991400. Use exponential backoff or other rate limiting strategies.
    - Document rate limit: 3 concurrent edits per second per document (includes create,
      update, delete operations). If exceeded, API returns HTTP 429.

    **Important Restrictions**:
    - Cannot delete table rows/columns or grid columns. Use update_document API with
      delete_table_rows/delete_table_columns operations instead.
    - Cannot delete all children of TableCell, GridColumn, or Callout blocks.
    - start_index must be less than end_index.

    Args:
        document_id: Document unique identifier (can be extracted from Feishu document URL).
            Example: "doxcnePuYufKa49ISjhD8Iabcef"
        block_id: Parent block ID whose children will be deleted. You can get block_id by
            calling get_document_blocks API. For root-level deletion, use document_id.
            Example: "doxcnO6UW6wAw2qIcYf4hZabcef"
        start_index: Starting index for deletion (inclusive, left-closed interval).
            Must be >= 0. Example: 0
        end_index: Ending index for deletion (exclusive, right-open interval).
            Must be > start_index. Example: 1
        document_revision_id: Document version to operate on. -1 means latest version.
            Document version starts from 1. To query latest version, requires document read permission.
            To query historical version, requires document edit permission. Default: -1
        client_token: Client token for idempotency (optional). If provided, the operation will be
            idempotent. Leave empty to initiate a new request.

    Example:
        # Delete the first child block (index 0) of a parent block
        delete_blocks(
            document_id="doxcnePuYufKa49ISjhD8Iabcef",
            block_id="doxcnO6UW6wAw2qIcYf4hZabcef",
            start_index=0,
            end_index=1
        )

        # Delete blocks from index 2 to 5 (deletes blocks at indices 2, 3, 4)
        delete_blocks(
            document_id="doxcnePuYufKa49ISjhD8Iabcef",
            block_id="doxcnO6UW6wAw2qIcYf4hZabcef",
            start_index=2,
            end_index=5
        )

    Returns:
        Dictionary containing:
        - success: Boolean indicating if operation succeeded
        - message: Status message
        - document_revision_id: Document version after deletion
        - client_token: Client token for idempotency (if provided)

    Note:
        The deletion operation uses a left-closed, right-open interval [start_index, end_index).
        This means:
        - start_index is inclusive (the block at start_index will be deleted)
        - end_index is exclusive (the block at end_index will NOT be deleted)
        - Example: start_index=0, end_index=3 deletes blocks at indices 0, 1, 2 (3 blocks total)
    """
    return await document_service.delete_blocks(
        document_id=document_id,
        block_id=block_id,
        start_index=start_index,
        end_index=end_index,
        document_revision_id=document_revision_id,
        client_token=client_token if client_token else None,
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
