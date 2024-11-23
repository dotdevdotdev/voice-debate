"""Speech processing module for VoiceDebate."""

import asyncio
import logging
import numpy as np
import sounddevice as sd
import requests
import io
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource
)
from voicedebate.config import config

logger = logging.getLogger(__name__)

# Configure API keys
deepgram = DeepgramClient(config.api.deepgram_api_key)

class AudioCapture:
    """Audio capture handler."""
    
    def __init__(self, sample_rate=16000, channels=1, dtype=np.int16):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.stream = None
        self.recording = False
        self._buffer = []
        
    async def start_recording(self):
        """Start recording audio."""
        if self.recording:
            return
        
        self.recording = True
        self._buffer = []
        
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio callback status: {status}")
            if self.recording:
                self._buffer.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            callback=callback
        )
        self.stream.start()
    
    async def stop_recording(self) -> np.ndarray:
        """Stop recording and return the audio data."""
        if not self.recording:
            return np.array([], dtype=self.dtype)
        
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        if not self._buffer:
            return np.array([], dtype=self.dtype)
        
        audio_data = np.concatenate(self._buffer)
        self._buffer = []
        return audio_data

class SpeechProcessor:
    """Speech processing handler."""
    
    API_BASE = "https://api.elevenlabs.io/v1"
    CHUNK_SIZE = 1024
    
    def __init__(self):
        self.audio_capture = AudioCapture()
        self._api_key = config.api.elevenlabs_api_key
        if not self._api_key:
            raise ValueError("ElevenLabs API key not found in config")
        
        self._model_id = "eleven_monolingual_v1"
    
    async def transcribe_audio(self, audio_data: np.ndarray) -> dict:
        """Transcribe audio data using Deepgram."""
        try:
            # Convert audio data to bytes
            audio_bytes = audio_data.tobytes()
            
            # Configure Deepgram options
            options = PrerecordedOptions(
                model="general",
                language="en",
                smart_format=True,
                punctuate=True
            )
            
            source = FileSource(buffer=audio_bytes, mimetype="audio/raw")
            response = await deepgram.transcribe(source, options)
            
            # Extract transcription results
            alternatives = response["results"]["channels"][0]["alternatives"]
            if alternatives:
                result = {
                    "text": alternatives[0]["transcript"],
                    "confidence": alternatives[0]["confidence"],
                    "words": alternatives[0].get("words", [])
                }
            else:
                result = {"text": "", "confidence": 0.0, "words": []}
            return result
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {"text": "", "confidence": 0.0, "words": []}
    
    async def synthesize_speech(self, text: str, voice_id: str, 
                              stability: float = 0.5, 
                              clarity: float = 0.75,
                              style: float = 0.0) -> bytes:
        """Synthesize speech using ElevenLabs."""
        try:
            # Set up request
            url = f"{self.API_BASE}/text-to-speech/{voice_id}/stream"
            headers = {
                "Accept": "application/json",
                "xi-api-key": self._api_key
            }
            data = {
                "text": text,
                "model_id": self._model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": clarity,
                    "style": style,
                    "use_speaker_boost": True
                }
            }
            
            # Make request in thread pool since it's blocking
            def make_request():
                response = requests.post(url, headers=headers, json=data, stream=True)
                if not response.ok:
                    raise RuntimeError(f"ElevenLabs API error: {response.text}")
                
                # Read all chunks into bytes
                audio_data = b""
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    audio_data += chunk
                return audio_data
            
            # Run in thread pool
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None, make_request
            )
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Speech synthesis error: {e}")
            return bytes()
    
    async def start_capture(self):
        """Start audio capture."""
        await self.audio_capture.start_recording()
    
    async def stop_capture(self) -> tuple[np.ndarray, dict]:
        """Stop audio capture and return audio data with transcription."""
        audio_data = await self.audio_capture.stop_recording()
        if len(audio_data) > 0:
            transcription = await self.transcribe_audio(audio_data)
        else:
            transcription = {"text": "", "confidence": 0.0, "words": []}
        return audio_data, transcription

# Global speech processor instance
speech_processor = SpeechProcessor()
