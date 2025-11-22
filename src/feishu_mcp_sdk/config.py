"""Configuration management using Pydantic Settings."""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from feishu_mcp_sdk.exceptions import ConfigurationError


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
    )

    # MCP Server Configuration
    mcp_server_name: str = Field(default="feishu_mcp", alias="MCP_SERVER_NAME")
    mcp_port: int = Field(default=8001, alias="MCP_PORT")

    # Feishu OAuth Configuration
    app_id: str = Field(default="", alias="APP_ID")
    app_secret: str = Field(default="", alias="APP_SECRET")

    @model_validator(mode="after")
    def validate_required_credentials(self):
        """Validate that required OAuth credentials are provided."""
        missing_fields = []
        if not self.app_id or not self.app_id.strip():
            missing_fields.append("APP_ID")
        if not self.app_secret or not self.app_secret.strip():
            missing_fields.append("APP_SECRET")

        if missing_fields:
            fields_str = " and ".join(missing_fields)
            raise ConfigurationError(
                f"Required configuration fields are missing or empty: {fields_str}. "
                f"Please set these environment variables or add them to your .env file."
            )

        return self

    # Feishu API Configuration
    host: str = Field(default="https://open.feishu.cn/open-apis/", alias="HOST")

    # OAuth Callback Server Configuration
    oauth_redirect_uri: str = Field(default="/oauth/callback", alias="OAUTH_REDIRECT_URI")
    oauth_callback_port: int = Field(default=8089, alias="OAUTH_CALLBACK_PORT")

    # OAuth Configuration
    oauth_authorize_url: str = Field(
        default="https://accounts.feishu.cn/open-apis/authen/v1/authorize",
        alias="OAUTH_AUTHORIZE_URL",
    )
    oauth_token_url: str = Field(
        default="https://open.feishu.cn/open-apis/authen/v2/oauth/token",
        alias="OAUTH_TOKEN_URL",
    )

    oauth_scope: str = Field(default="docs:doc drive:drive docx:document", alias="OAUTH_SCOPE")

    # Read-only mode configuration
    read_only_mode: bool = Field(default=False, alias="READ_ONLY_MODE")


def get_settings() -> Settings:
    """Get the application settings instance."""
    return Settings()


settings = get_settings()
