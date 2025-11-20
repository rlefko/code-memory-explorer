"""
Configuration settings for the Claude Code Memory Explorer API.
Loads from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load settings.txt from backend directory for API keys
SETTINGS_FILE = Path(__file__).parent / "settings.txt"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_title: str = "Claude Code Memory Explorer"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_timeout: int = 30

    # Search Configuration
    default_search_limit: int = 20
    max_search_limit: int = 100
    search_mode_default: str = "hybrid"  # semantic, keyword, hybrid

    # Token Limits (for MCP compliance)
    max_response_tokens: int = 23000  # 92% of 25k MCP limit
    token_estimate_ratio: float = 0.25  # 1 token per 4 chars

    # WebSocket Configuration
    ws_ping_interval: int = 30
    ws_max_connections: int = 100

    # Development Settings
    debug: bool = False
    reload: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self):
        super().__init__()
        self._load_settings_file()

    def _load_settings_file(self):
        """Load API keys from settings.txt if it exists."""
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()

                            # Map settings.txt keys to our config
                            if key == "QDRANT_URL":
                                self.qdrant_url = value
                            elif key == "QDRANT_API_KEY":
                                self.qdrant_api_key = value if value != "None" else None


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings