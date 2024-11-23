[Previous sections remain the same through Project Structure]

## Development Environment

### Requirements
- Python 3.10+ (for modern async support and type hints)
- Virtual environment management (venv or conda)
- Git for version control

### Core Dependencies
```
kivy~=2.2.1
kivymd~=1.1.1
audiostream~=0.3
python-dotenv~=1.0.0

# Speech Services
deepgram-sdk~=2.11.0
elevenlabs~=0.2.24

# AI Services
anthropic~=0.8.0  # For Claude Haiku
openai~=1.12.0    # For GPT-4-Turbo
```

### Platform-Specific Requirements

#### Windows
- Visual C++ build tools
- PyAudio dependencies (automatically handled by audiostream)
- KIVY_GL_BACKEND=angle (recommended for better performance)

#### macOS
- Xcode command line tools
- Homebrew (recommended for dependency management)
- portaudio (`brew install portaudio`)

#### Linux
- Python dev package (`python3.10-dev`)
- PortAudio dev (`libportaudio2`)
- ALSA dev packages (`libasound-dev`)

## API Integration Patterns

### Speech-to-Text (Deepgram)
```python
class DeepgramManager:
    def __init__(self, api_key: str):
        self.client = Deepgram(api_key)
        
    async def create_stream(self):
        options = {
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1,
            "language": "en",
            "model": "nova-2",
            "smart_format": True
        }
        return await self.client.transcription.live(options)
```

### Text-to-Speech (ElevenLabs)
```python
class ElevenLabsManager:
    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key)
        
    async def generate_speech(
        self, 
        text: str, 
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice
        model_id: str = "eleven_turbo_v2"
    ):
        try:
            audio = await self.client.generate(
                text=text,
                voice_id=voice_id,
                model_id=model_id
            )
            return audio
        except Exception as e:
            self.dispatch(VoiceDebateEvents.ON_AUDIO_ERROR, str(e))
```

### AI Service Integration
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class DebateMessage:
    role: str
    content: str
    name: Optional[str] = None

class AIProvider(ABC):
    @abstractmethod
    async def generate_response(
        self, 
        messages: List[DebateMessage],
        temperature: float = 0.7
    ) -> str:
        pass

class ClaudeHaikuProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.Client(api_key=api_key)
        
    async def generate_response(
        self, 
        messages: List[DebateMessage],
        temperature: float = 0.7
    ) -> str:
        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        response = await self.client.messages.create(
            model="claude-3-haiku-20240307",
            messages=formatted_messages,
            temperature=temperature
        )
        return response.content

class GPTTurboProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
    async def generate_response(
        self, 
        messages: List[DebateMessage],
        temperature: float = 0.7
    ) -> str:
        formatted_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        response = await self.client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=formatted_messages,
            temperature=temperature
        )
        return response.choices[0].message.content

# Factory for creating AI providers
class AIProviderFactory:
    @staticmethod
    def create_provider(provider_type: str, api_key: str) -> AIProvider:
        if provider_type.lower() == "claude":
            return ClaudeHaikuProvider(api_key)
        elif provider_type.lower() == "gpt":
            return GPTTurboProvider(api_key)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
```

[Previous sections remain the same through Resource Management]

## Testing Guidelines

### Basic Test Cases
1. Audio Pipeline
   - Capture audio for 5 seconds
   - Verify buffer management
   - Test playback quality

2. Speech Services
   - Test Deepgram transcription accuracy
   - Verify ElevenLabs voice consistency
   - Measure latency and performance

3. AI Integration
   - Test response generation
   - Verify context management
   - Check error handling

## Configuration
```python
# config/settings.py
from typing import Literal
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Keys
    DEEPGRAM_API_KEY: str
    ELEVENLABS_API_KEY: str
    AI_PROVIDER: Literal["claude", "gpt"] = "claude"
    AI_API_KEY: str
    
    # Audio Settings
    SAMPLE_RATE: int = 16000
    CHUNK_SIZE: int = 1024
    CHANNELS: int = 1
    
    # UI Settings
    THEME_STYLE: Literal["light", "dark"] = "dark"
    PRIMARY_PALETTE: str = "Blue"
    
    class Config:
        env_file = ".env"
```

[Previous sections remain the same]
