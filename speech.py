"""Speech services for VoiceDebate."""

import asyncio
import logging
from typing import AsyncGenerator, Optional, Callable
import sounddevice as sd
import numpy as np
from deepgram import Deepgram
from elevenlabs import generate, stream
from .config import config

logger = logging.getLogger(__name__)

class AudioCapture:
    """Audio capture handler."""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self._buffer = asyncio.Queue()
    
    def callback(self, indata: np.ndarray, frames: int, time, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio capture status: {status}")
        if self.is_recording:
            self._buffer.put_nowait(bytes(indata))
    
    async def start(self):
        """Start audio capture."""
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.int16,
            callback=self.callback
        )
        self.stream.start()
    
    async def stop(self):
        """Stop audio capture."""
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    async def get_audio(self) -> AsyncGenerator[bytes, None]:
        """Get audio data from the buffer."""
        while self.is_recording:
            try:
                chunk = await asyncio.wait_for(self._buffer.get(), timeout=0.1)
                yield chunk
            except asyncio.TimeoutError:
                continue

class TranscriptionService:
    """Deepgram transcription service."""
    
    def __init__(self):
        self.client = Deepgram(config.api.deepgram_api_key)
        self.connection = None
    
    async def start_stream(self, callback: Callable[[dict], None]):
        """Start transcription stream."""
        options = {
            "encoding": "linear16",
            "sample_rate": 16000,
            "channels": 1,
            "language": "en-US",
            "model": "nova",
            "interim_results": True,
        }
        
        self.connection = await self.client.transcription.live(options)
        self.connection.registerHandler(self.connection.event.CLOSE, lambda c: logger.info("Connection closed."))
        self.connection.registerHandler(self.connection.event.TRANSCRIPT_RECEIVED, callback)
        
        return self.connection
    
    async def stop_stream(self):
        """Stop transcription stream."""
        if self.connection:
            await self.connection.finish()
            self.connection = None

class SpeechSynthesisService:
    """ElevenLabs speech synthesis service."""
    
    def __init__(self):
        self.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    
    async def synthesize_speech(self, text: str, voice_id: str) -> AsyncGenerator[bytes, None]:
        """Synthesize speech from text."""
        audio_stream = generate(
            text=text,
            voice=voice_id,
            model="eleven_monolingual_v1",
            stream=True
        )
        
        for chunk in audio_stream:
            yield chunk
    
    async def play_audio(self, audio_stream: AsyncGenerator[bytes, None]):
        """Play audio from stream."""
        # Note: This is a simplified implementation
        # In production, we would need proper audio format handling
        chunks = []
        async for chunk in audio_stream:
            chunks.append(chunk)
        
        audio_data = b"".join(chunks)
        # Convert audio_data to numpy array and play with sounddevice
        # This would need proper audio format conversion
