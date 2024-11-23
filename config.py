"""Configuration management for VoiceDebate."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConfig(BaseModel):
    """Database configuration."""
    type: str = Field(default="sqlite", pattern="^(sqlite|postgresql)$")
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "voicedebate.db"
    username: Optional[str] = None
    password: Optional[str] = None

class APIConfig(BaseModel):
    """API keys and configurations."""
    deepgram_api_key: str = Field(default_factory=lambda: os.getenv("DEEPGRAM_API_KEY", ""))
    elevenlabs_api_key: str = Field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

class ThemeConfig(BaseModel):
    """UI theme configuration."""
    colors = {
        'background': '#000000',  # Solid black
        'primary': '#39FF14',     # Neon green
        'secondary': '#00BFFF',   # Neon blue
        'surface': '#111111',     # Slightly lighter black for cards
        'text_primary': '#39FF14',
        'text_secondary': '#00BFFF',
    }
    theme_style: str = "Dark"
    primary_palette: str = "Green"
    accent_palette: str = "Blue"

class Config(BaseModel):
    """Main application configuration."""
    app_name: str = "VoiceDebate"
    version: str = "0.1.0"
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".voicedebate")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    theme: ThemeConfig = Field(default_factory=ThemeConfig)

    def ensure_data_dir(self):
        """Ensure the data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir

# Global configuration instance
config = Config()
config.ensure_data_dir()
