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

1. **Important: Configure Feishu App Permissions**

   Before using this SDK, you need to create a Feishu app and configure the required permissions:
   
   - Go to [Feishu Open Platform](https://open.feishu.cn/app)
   - Create a new app or select an existing one
   - Navigate to **Permissions & Scopes** (权限管理)
   - Enable the following permissions that match the `OAUTH_SCOPE`:
     - `docs:doc` - View documents
     - `drive:drive` - View drive files
     - `docx:document` - View and edit Docx documents
   
   **Note**: Without these permissions, the OAuth flow will fail or the API calls will return permission errors.

2. Copy the example environment file:
```bash
cp .env.example .env
```

3. Edit `.env` with your Feishu credentials:
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
uvx python -m feishu_mcp_sdk run mcp server

# Or using the entry script
uvx feishu-mcp

# Or run the Python module directly
uvx python -m feishu_mcp_sdk.server
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
from feishu_mcp_sdk import run_server
import asyncio

# Run server directly
asyncio.run(run_server(transport="stdio"))
```

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
# Lint and fix code
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

