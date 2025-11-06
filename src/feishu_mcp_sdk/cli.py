"""Command-line interface for Feishu MCP SDK."""

import anyio
import typer

from feishu_mcp_sdk.server import run_server

app = typer.Typer(help="Feishu MCP SDK CLI")


@app.command()
def server(
    transport: str = typer.Option(
        "stdio",
        "--transport",
        "-t",
        help="Transport mode: 'stdio' or 'streamable-http' (default: stdio)",
    ),
):
    """
    Run the MCP server.

    Supports two transport modes:
    - stdio: Standard input/output transport (default)
    - streamable-http: Streamable HTTP transport
    """
    anyio.run(run_server, transport)


def main() -> None:
    """Main CLI entry point."""
    app()
