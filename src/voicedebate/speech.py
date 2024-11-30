"""Speech processing module for VoiceDebate."""

import asyncio
import logging
import numpy as np
import sounddevice as sd
import requests
import io
import wave
from scipy import signal
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from voicedebate.config import config

logger = logging.getLogger(__name__)

# Configure API keys with options
dg = DeepgramClient(
    api_key=config.api.deepgram_api_key,
)


class SpeechProcessor:
    """Speech processing handler."""

    API_BASE = "https://api.elevenlabs.io/v1"
    CHUNK_SIZE = 1024
    TARGET_SAMPLE_RATE = 16000

    def __init__(self):
        self._api_key = config.api.elevenlabs_api_key
        if not self._api_key:
            raise ValueError("ElevenLabs API key not found in config")

        self._model_id = "eleven_monolingual_v1"
        self.dg_connection = None
        self.microphone = None
        self.current_transcript = ""
        self._transcript_callback = None

    async def start_capture(self, transcript_callback=None):
        """Start audio capture with live transcription."""
        try:
            # Clear the transcript when starting new recording
            self.current_transcript = ""

            self._transcript_callback = transcript_callback
            self.dg_connection = dg.listen.live.v("1")

            # Set up event handlers
            self.dg_connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.dg_connection.on(
                LiveTranscriptionEvents.Transcript, self._on_transcript
            )
            self.dg_connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.dg_connection.on(LiveTranscriptionEvents.Close, self._on_close)

            # Configure transcription options
            options = LiveOptions(
                model="nova-2",
                punctuate=True,
                language="en-US",
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
            )

            # Start the connection without awaiting
            self.dg_connection.start(options)
            logger.info("Deepgram connection started")

            # Start the microphone with the correct send method
            self.microphone = Microphone(self.dg_connection.send)
            self.microphone.start()
            logger.info("Microphone started")

        except Exception as e:
            logger.error(f"Error starting capture: {e}")
            raise

    async def stop_capture(self) -> tuple[np.ndarray, dict]:
        """Stop audio capture and return final transcription."""
        try:
            if self.microphone:
                self.microphone.finish()

            if self.dg_connection:
                # Don't await the finish call
                self.dg_connection.finish()

            # Return the final transcript
            return np.array([]), {
                "text": self.current_transcript,
                "confidence": 1.0,
                "words": [],
            }

        except Exception as e:
            logger.error(f"Error stopping capture: {e}")
            return np.array([]), {"text": "", "confidence": 0.0, "words": []}

    def _on_open(self, *args, **kwargs):
        """Handle websocket open event."""
        logger.info("Deepgram connection opened")

    def _on_transcript(self, *args, **kwargs):
        """Handle transcript event."""
        try:
            # Get the result from kwargs
            result = kwargs.get("result")
            if not result:
                return

            # Get the transcript from the result
            transcript = result.channel.alternatives[0].transcript
            if transcript:
                logger.info(f"Got transcript: {transcript}")

                # Only append if this is a final result
                if result.is_final:
                    self.current_transcript += " " + transcript.strip()
                    self.current_transcript = self.current_transcript.strip()

                if self._transcript_callback:
                    # Use Kivy's Clock instead of asyncio
                    from kivy.clock import Clock

                    # Show current transcript + interim result in UI
                    display_text = self.current_transcript
                    if not result.is_final:
                        display_text += " " + transcript.strip()
                    Clock.schedule_once(
                        lambda dt: self._transcript_callback(display_text.strip()), 0
                    )

        except Exception as e:
            logger.error(f"Error handling transcript: {e}", exc_info=True)
            logger.error(f"Args: {args}")
            logger.error(f"Kwargs: {kwargs}")

    def _on_error(self, *args, **kwargs):
        """Handle error event."""
        error = kwargs.get("data", {})
        logger.error(f"Deepgram error: {error}")

    def _on_close(self, *args, **kwargs):
        """Handle websocket close event."""
        logger.info("Deepgram connection closed")

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        stability: float = 0.5,
        clarity: float = 0.75,
        style: float = 0.0,
    ) -> bytes:
        """Synthesize speech using ElevenLabs."""
        try:
            # Set up request
            url = f"{self.API_BASE}/text-to-speech/{voice_id}/stream"
            headers = {"Accept": "application/json", "xi-api-key": self._api_key}
            data = {
                "text": text,
                "model_id": self._model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": clarity,
                    "style": style,
                    "use_speaker_boost": True,
                },
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


# Global speech processor instance
speech_processor = SpeechProcessor()
