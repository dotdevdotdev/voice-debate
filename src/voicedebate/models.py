"""Database models for VoiceDebate."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class User(BaseModel):
    """User model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DebateSession(BaseModel):
    """Debate session model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    topic: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: uuid.UUID
    status: str = Field(default="active", pattern="^(active|completed|archived)$")

class Transcription(BaseModel):
    """Transcription model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    speaker_id: uuid.UUID
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: Optional[float] = None
    is_final: bool = False

class AudioSegment(BaseModel):
    """Audio segment model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    session_id: uuid.UUID
    speaker_id: uuid.UUID
    audio_data: bytes
    duration: int  # in milliseconds
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AssistantConfig(BaseModel):
    """AI Assistant configuration."""
    name: str
    description: str
    system_prompt: str
    provider: str = Field(pattern="^(claude|gpt)$")
    model: str
    temperature: float = 0.7
    voice_id: str
    voice_stability: float = 0.5
    voice_clarity: float = 0.75
    voice_style: float = 0.0
