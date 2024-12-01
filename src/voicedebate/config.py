"""Configuration management for VoiceDebate."""

import os
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel


class APIConfig(BaseModel):
    """API configuration."""

    anthropic_api_key: str
    openai_api_key: str
    elevenlabs_api_key: str
    deepgram_api_key: str


class ThemeConfig(BaseModel):
    """Theme configuration."""

    theme_style: str = "Dark"
    primary_palette: str = "BlueGray"
    accent_palette: str = "Amber"
    colors: Dict[str, str] = {
        "background": "#121212",
        "surface": "#1E1E1E",
        "primary": "#607D8B",
        "secondary": "#FFC107",
    }


class Config(BaseModel):
    """Main configuration."""

    api: APIConfig
    theme: ThemeConfig
    data_dir: Path = Path.home() / ".voicedebate" / "data"


# Load configuration
config = Config(
    api=APIConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        deepgram_api_key=os.getenv("DEEPGRAM_API_KEY", ""),
    ),
    theme=ThemeConfig(),
)
