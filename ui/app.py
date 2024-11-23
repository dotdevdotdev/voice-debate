"""Main application UI."""

import asyncio
from functools import partial
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import MDList, OneLineListItem

from ..config import config
from ..database import db
from ..assistant import AssistantManager, AIClient
from ..speech import AudioCapture, TranscriptionService, SpeechSynthesisService

class ChatMessage(MDBoxLayout):
    """Chat message widget."""
    
    def __init__(self, speaker_name: str, message_text: str, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = "8dp"
        self.spacing = "4dp"
        
        speaker_label = MDLabel(
            text=speaker_name,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=config.theme.colors["text_secondary"]
        )
        
        message_label = MDLabel(
            text=message_text,
            theme_text_color="Custom",
            text_color=config.theme.colors["text_primary"]
        )
        
        self.add_widget(speaker_label)
        self.add_widget(message_label)

class ChatArea(MDBoxLayout):
    """Chat area widget."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = "8dp"
        self.spacing = "8dp"
        
        # Message list
        self.scroll_list = MDList()
        self.add_widget(self.scroll_list)
        
        # Control area
        controls = MDCard(
            size_hint_y=None,
            height="60dp",
            padding="8dp"
        )
        
        self.record_button = MDFillRoundFlatIconButton(
            icon="microphone",
            text="Start Recording",
            on_press=self.toggle_recording
        )
        
        self.status_label = MDLabel(
            text="Ready",
            theme_text_color="Custom",
            text_color=config.theme.colors["text_secondary"]
        )
        
        controls.add_widget(self.record_button)
        controls.add_widget(self.status_label)
        self.add_widget(controls)
        
        # Services
        self.audio_capture = AudioCapture()
        self.transcription = TranscriptionService()
        self.synthesis = SpeechSynthesisService()
        self.is_recording = False
    
    def add_message(self, speaker: str, message: str):
        """Add a message to the chat."""
        self.scroll_list.add_widget(ChatMessage(speaker, message))
    
    def toggle_recording(self, *args):
        """Toggle recording state."""
        if not self.is_recording:
            asyncio.create_task(self.start_recording())
        else:
            asyncio.create_task(self.stop_recording())
    
    async def start_recording(self):
        """Start recording and transcription."""
        self.is_recording = True
        self.record_button.text = "Stop Recording"
        self.status_label.text = "Recording..."
        
        await self.audio_capture.start()
        connection = await self.transcription.start_stream(self.handle_transcript)
        
        async for chunk in self.audio_capture.get_audio():
            if not self.is_recording:
                break
            connection.send(chunk)
    
    async def stop_recording(self):
        """Stop recording and transcription."""
        self.is_recording = False
        self.record_button.text = "Start Recording"
        self.status_label.text = "Processing..."
        
        await self.audio_capture.stop()
        await self.transcription.stop_stream()
        self.status_label.text = "Ready"
    
    def handle_transcript(self, transcript: dict):
        """Handle transcription results."""
        if not transcript.get("is_final"):
            return
        
        text = transcript["channel"]["alternatives"][0]["transcript"]
        if text.strip():
            self.add_message("You", text)
            asyncio.create_task(self.get_ai_response(text))
    
    async def get_ai_response(self, message: str):
        """Get and speak AI response."""
        response = await app.ai_client.get_response(message)
        self.add_message(app.ai_client.assistant.name, response)
        
        audio_stream = self.synthesis.synthesize_speech(
            response,
            app.ai_client.assistant.voice_id
        )
        await self.synthesis.play_audio(audio_stream)

class VoiceDebateApp(MDApp):
    """Main application class."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assistant_manager = AssistantManager()
        self.ai_client = None
        self.chat_area = None
    
    def build(self):
        """Build the application UI."""
        # Set theme
        self.theme_cls.theme_style = config.theme.theme_style
        self.theme_cls.primary_palette = config.theme.primary_palette
        self.theme_cls.accent_palette = config.theme.accent_palette
        
        # Create main screen
        screen = MDScreen()
        
        # Create chat area
        self.chat_area = ChatArea()
        screen.add_widget(self.chat_area)
        
        # Show assistant selection on start
        self.select_assistant()
        
        return screen
    
    def select_assistant(self, *args):
        """Show assistant selection dialog."""
        if not self.assistant_manager.get_assistant_names():
            self.assistant_manager.create_default_assistants()
        
        content = MDList()
        for name in self.assistant_manager.get_assistant_names():
            item = OneLineListItem(
                text=name,
                on_release=partial(self.on_assistant_selected, name)
            )
            content.add_widget(item)
        
        self.dialog = MDDialog(
            title="Select AI Assistant",
            type="custom",
            content_cls=content,
            size_hint=(.8, None)
        )
        self.dialog.open()
    
    def on_assistant_selected(self, name: str, *args):
        """Handle assistant selection."""
        self.dialog.dismiss()
        assistant = self.assistant_manager.get_assistant(name)
        if assistant:
            self.ai_client = AIClient(assistant)
            self.chat_area.add_message(
                "System",
                f"Selected assistant: {assistant.name}\n{assistant.description}"
            )

async def main():
    """Initialize and run the application."""
    # Initialize database
    await db.initialize()
    
    # Start application
    app = VoiceDebateApp()
    app.run()

if __name__ == "__main__":
    asyncio.run(main())
