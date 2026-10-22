"""Configuration settings for A11y Agent using Pydantic Settings."""

import os
from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = "A11y Agent"
    version: str = "1.0.0"
    env: str = "development"
    debug: bool = False

    # Crawler & Network
    user_agent: str = "A11yAgent/1.0 (+https://github.com/a11y-agent/bot; accessibility audit bot)"
    request_timeout: int = 30  # seconds
    max_page_size_bytes: int = 15 * 1024 * 1024  # 15 MB
    respect_robots_txt: bool = True
    allow_private_ips: bool = False  # Strict SSRF protection by default

    # LLM Settings
    llm_provider: Literal["auto", "openai", "anthropic", "gemini", "mock"] = "auto"
    llm_model: Optional[str] = None
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    # Storage paths
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    reports_dir: Path = base_dir / "reports"
    screenshots_dir: Path = base_dir / "reports" / "screenshots"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_directories(self) -> None:
        """Ensure necessary output directories exist."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_directories()
