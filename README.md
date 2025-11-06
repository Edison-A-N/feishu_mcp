# Feishu MCP SDK

A Model Context Protocol (MCP) server for Feishu Document integration, allowing AI assistants to query and interact with Feishu documents.

## Features

- 🔐 OAuth2 authentication with Feishu
- 📄 List, search, and manage Feishu documents
- 📖 Get document content and blocks with pagination
- ✏️ Update document content
- 🔄 Automatic token refresh on expiration
- 🚀 FastMCP-based server implementation
- 🌐 CORS-enabled for web clients

## Installation

### Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### Using pip

```bash
pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env.local
```

2. Edit `.env.local` with your Feishu credentials:
```env
# MCP Server Configuration
MCP_SERVER_NAME=feishu_mcp
MCP_PORT=8001

# Feishu OAuth Configuration
# Get these from https://open.feishu.cn/app
APP_ID=your_app_id_here
APP_SECRET=your_app_secret_here

# Feishu API Configuration
HOST=https://open.feishu.cn/open-apis/

# OAuth Callback Server Configuration
# Note: OAUTH_REDIRECT_URI should be a path only (e.g., /oauth/callback)
# The full URL will be constructed as: http://localhost:{OAUTH_CALLBACK_PORT}{OAUTH_REDIRECT_URI}
OAUTH_REDIRECT_URI=/oauth/callback
OAUTH_CALLBACK_PORT=8089

# OAuth Configuration (optional, defaults are usually fine)
OAUTH_AUTHORIZE_URL=https://accounts.feishu.cn/open-apis/authen/v1/authorize
OAUTH_TOKEN_URL=https://open.feishu.cn/open-apis/authen/v2/oauth/token
OAUTH_SCOPE=docs:doc drive:drive docx:document
```

## Usage

### Running the MCP Server

#### Using uvx (Recommended for local development)

```bash
# Elegant way: run mcp server
uvx --with-editable . python -m feishu_mcp_sdk run mcp server

# Or using the entry script
uvx --with-editable . feishu-mcp

# Or run the Python module directly
uvx --with-editable . python -m feishu_mcp_sdk.server
```

#### Using installed script

```bash
# After installation (uv sync or pip install -e .)
feishu-mcp

# Or directly
python -m feishu_mcp_sdk.server
```

### As a Python Package

```python
from feishu_mcp_sdk import create_app, run_server
import asyncio

# Create app for integration
app = create_app()

# Or run server directly
asyncio.run(run_server(transport="stdio"))
```

## MCP Tools

### `list_documents`

List documents in a folder or root directory.

**Parameters:**
- `folder_token` (str, optional): Folder token (leave empty for root directory)
- `page_size` (int, default: 50): Number of items per page
- `page_token` (str, optional): Token for pagination

**Returns:** Dictionary containing document list and pagination info

### `get_document`

Get document content by document ID.

**Parameters:**
- `document_id` (str): Document token (can be extracted from Feishu document URL)
- `include_raw_content` (bool, default: False): Whether to include raw text content
- `lang` (int, default: 0): Language for MentionUser display (0=default, 1=English)

**Returns:** Dictionary containing document content and metadata

### `get_document_blocks`

Get all blocks of a document with pagination.

**Parameters:**
- `document_id` (str): Document unique identifier
- `page_size` (int, default: 500): Page size (max: 500)
- `page_token` (str, optional): Page token for pagination
- `document_revision_id` (int, default: -1): Document version to query (-1 means latest)
- `user_id_type` (str, default: "open_id"): User ID type (open_id, union_id, user_id)

**Returns:** Dictionary containing block information with pagination

### `get_document_info`

Get document basic information (title and latest revision ID).

**Parameters:**
- `document_id` (str): Document ID (can be extracted from Feishu document URL)

**Returns:** Dictionary containing document basic information

### `search_documents`

Search documents by query string.

**Parameters:**
- `query` (str): Search query string
- `page_size` (int, default: 50): Number of items per page
- `page_token` (str, optional): Token for pagination

**Returns:** Dictionary containing search results

### `update_document`

Update document content (append text to Docx document).

**Parameters:**
- `document_id` (str): Document token (can be extracted from Feishu document URL)
- `content` (str): Text content to add to the document
- `block_id` (str, optional): Block ID to insert after (leave empty to append to end)

**Returns:** Dictionary containing update result

**Note:** All document APIs have a rate limit of 5 requests per second per app. If exceeded, API returns HTTP 400 with error code 99991400.

## Development

### Setup

```bash
# Install with dev dependencies
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"
```

### Code Formatting

```bash
# Format code
black src/

# Lint code
ruff check src/
```

### Testing

Testing is not currently configured. To add tests in the future, you can:
- Add pytest to dev dependencies
- Create a `tests/` directory
- Write test files following pytest conventions

## Project Structure

```
feishu_mcp_sdk/
├── src/
│   └── feishu_mcp_sdk/
│       ├── __init__.py
│       ├── config.py              # Configuration management
│       ├── server.py               # MCP server implementation
│       ├── cli.py                  # Command-line interface
│       ├── api/
│       │   ├── client.py           # Feishu API client
│       │   ├── oauth_manager.py    # OAuth2 authentication
│       │   └── exceptions.py       # Custom exceptions
│       └── services/
│           ├── document_service.py # Document service
│           └── http_client_mixin.py # HTTP client mixin
├── pyproject.toml                  # Project configuration
├── .env.example                     # Example environment file
├── .env.local                       # Local environment (git-ignored)
├── .gitignore
├── LICENSE
└── README.md
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Nan Zhang - zhangn661@gmail.com

