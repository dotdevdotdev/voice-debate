"""Database models for VoiceDebate."""

import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass


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


@dataclass
class VoiceConfig:
    id: str
    stability: float
    clarity: float
    name: str


@dataclass
class SpeechStyle:
    patterns: List[str]
    vocabulary_level: str
    tone: str
    response_starters: List[str]
    scripted_responses: Dict[str, List[str]]


@dataclass
class CharacterDefinition:
    core_traits: List[str]
    background: str
    speech_style: SpeechStyle


@dataclass
class InteractionGuidelines:
    primary_goal: str
    conversation_strategy: str
    must_rules: List[str]
    must_not_rules: List[str]


@dataclass
class ModelConfig:
    provider: str
    model: str
    temperature: float


@dataclass
class CharacterMetadata:
    author: str
    version: str
    created: str
    tags: List[str]


@dataclass
class CharacterData:
    name: str
    description: str
    metadata: CharacterMetadata
    voice: VoiceConfig
    character_definition: CharacterDefinition
    interaction_guidelines: InteractionGuidelines
    system_prompt: str
    model_config: ModelConfig


class AssistantConfig(BaseModel):
    """Configuration for an AI assistant."""

    name: str
    description: str
    system_prompt: str
    provider: str
    model: str
    temperature: float

    # Voice settings
    voice_id: str
    voice_stability: float
    voice_clarity: float
    voice_style: float = 0.0  # Default style value for ElevenLabs

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
