"""Main application UI module."""

import asyncio
import logging
from functools import partial
from pathlib import Path
from typing import Optional
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.properties import ObjectProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineIconListItem, MDList
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.icon_definitions import md_icons
from voicedebate.config import config
from voicedebate.speech import SpeechProcessor, speech_processor
from voicedebate.assistant import AssistantManager, assistant_manager
import uuid
import random

logger = logging.getLogger(__name__)

# Define the UI layout using KV language
KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

<MessageCard>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: "16dp"
    spacing: "8dp"
    
    MDLabel:
        text: root.speaker
        theme_text_color: "Secondary"
        size_hint_y: None
        height: self.texture_size[1]
    
    MDLabel:
        text: root.message
        theme_text_color: "Primary"
        size_hint_y: None
        height: self.texture_size[1]

<DebateScreen>:
    chat_layout: chat_layout
    current_transcript_label: current_transcript_label
    
    MDBoxLayout:
        orientation: "vertical"
        spacing: "24dp"
        padding: "48dp"
        md_bg_color: get_color_from_hex(app.theme_cls.colors['background'])
        
        # Top bar with icons and text
        MDBoxLayout:
            size_hint_y: None
            height: "160dp"
            spacing: "24dp"
            padding: ["24dp", "0dp"]
            
            # Left icon
            MDIconButton:
                icon: "account-switch"
                on_release: root.show_assistant_dialog()
                icon_size: "64dp"
                size_hint: None, None
                size: "120dp", "120dp"
            
            # Center text
            MDLabel:
                text: root.current_assistant if root.current_assistant else "Select Assistant"
                theme_text_color: "Primary"
                font_size: "48sp"
                halign: "center"
                valign: "center"
            
            # Right icon
            MDIconButton:
                icon: "microphone"
                icon_size: "64dp"
                size_hint: None, None
                size: "120dp", "120dp"
        
        # Main content area
        MDScrollView:
            do_scroll_x: False
            
            MDList:
                id: chat_layout
                spacing: "16dp"
                padding: "16dp"
        
        # Real-time transcript area
        MDCard:
            size_hint_y: None
            height: "120dp"
            padding: "16dp"
            md_bg_color: get_color_from_hex(app.theme_cls.colors['surface'])
            
            MDLabel:
                id: current_transcript_label
                text: ""
                theme_text_color: "Primary"
                font_size: "24sp"
                halign: "left"
                valign: "center"
        
        # Bottom controls
        MDBoxLayout:
            size_hint_y: None
            height: "112dp"
            spacing: "16dp"
            
            MDRaisedButton:
                id: record_button
                text: "Start Recording"
                font_size: "48sp"
                size_hint: (None, None)
                size: "600dp", "160dp"
                pos_hint: {"center_x": 0.5}
                on_release: app.schedule_async(root.toggle_recording())
                md_bg_color: get_color_from_hex(app.theme_cls.colors['primary'])
"""


class MessageCard(MDCard):
    """Card widget for displaying chat messages."""

    speaker = StringProperty()
    message = StringProperty()


class DebateScreen(MDScreen):
    """Main debate screen."""

    chat_layout = ObjectProperty(None)
    current_assistant = StringProperty("")
    _recording = False
    _assistant_dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None  # Will be set by VoiceDebateApp.build()
        self._recording = False
        self._assistant_dialog = None

    def add_message(self, speaker: str, message: str):
        """Add a message to the chat."""
        card = MessageCard(speaker=speaker, message=message)
        self.chat_layout.add_widget(card)

        # Scroll to bottom
        def scroll_bottom(*args):
            scroll_view = self.chat_layout.parent
            scroll_view.scroll_y = 0

        Clock.schedule_once(scroll_bottom, 0.1)

    def handle_transcript(self, text: str):
        """Handle real-time transcript updates."""
        logger.debug(f"Handling transcript update: {text}")
        if hasattr(self, "current_transcript_label"):
            logger.debug(f"Updating transcript label to: {text}")
            self.current_transcript_label.text = text.strip()
        else:
            logger.warning("current_transcript_label not found")

    async def toggle_recording(self):
        """Toggle audio recording state."""
        try:
            if not self._recording:
                await self.app.speech_processor.start_capture(self.handle_transcript)
                self._recording = True
                self.ids.record_button.text = "Stop Recording"
                self.ids.record_button.md_bg_color = self.theme_cls.colors["secondary"]
            else:
                _, transcription = await self.app.speech_processor.stop_capture()
                self._recording = False
                self.ids.record_button.text = "Start Recording"
                self.ids.record_button.md_bg_color = self.theme_cls.colors["primary"]

                if transcription.get("text"):
                    user_text = transcription["text"]
                    # Add user message immediately
                    self.add_message("You", user_text)

                    # Get AI response in the background
                    if self.current_assistant:
                        asyncio.create_task(
                            self._get_and_display_ai_response(user_text)
                        )

        except Exception as e:
            logger.error(f"Error in recording toggle: {e}")
            self._recording = False

    async def _get_and_display_ai_response(self, user_text: str):
        """Get and display AI response in the background."""
        try:
            assistant = self.app.assistant_manager.get_assistant(self.current_assistant)
            if assistant:
                # Show "thinking" message
                self.add_message(self.current_assistant, "Thinking...")

                # Get AI response
                response_text = await assistant.generate_response(user_text)

                # Update the "thinking" message with actual response
                last_card = self.chat_layout.children[0]
                if isinstance(last_card, MessageCard):
                    last_card.message = response_text

                # Synthesize and play audio
                audio = await self.app.speech_processor.synthesize_speech(
                    text=response_text,
                    voice_id=assistant.config.voice_id,
                    stability=assistant.config.voice_stability,
                    clarity=assistant.config.voice_clarity,
                    style=assistant.config.voice_style,
                )

                if audio:
                    try:
                        # Use the app's temp audio path
                        temp_path = (
                            Path(config.data_dir)
                            / f"temp_audio_{self.app.instance_id}.wav"
                        )
                        temp_path.write_bytes(audio)

                        # Play audio
                        sound = SoundLoader.load(str(temp_path))
                        if sound:
                            sound.play()
                        else:
                            logger.error("Failed to load audio file")
                    except Exception as e:
                        logger.error(f"Error playing audio: {e}")

        except Exception as e:
            logger.error(f"Error getting AI response: {e}")

    def show_assistant_dialog(self):
        """Show dialog to select AI assistant."""
        if not self._assistant_dialog:
            items = []
            for name in self.app.assistant_manager.list_assistants():
                item = OneLineIconListItem(
                    text=name.title(),
                    font_style="H3",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x, n=name: self.select_assistant(n),
                    _height="120dp",
                    divider="Full",
                    divider_color=self.theme_cls.primary_color,
                )
                items.append(item)

            self._assistant_dialog = MDDialog(
                title="Select AI Assistant",
                type="simple",
                items=items,
                size_hint=(0.9, 0.9),
                md_bg_color=self.theme_cls.bg_dark,
                radius=[20, 20, 20, 20],
                elevation=10,
            )

            # Set title font size through the widget after creation
            if (
                hasattr(self._assistant_dialog, "ids")
                and "title" in self._assistant_dialog.ids
            ):
                self._assistant_dialog.ids.title.font_size = "64sp"

        self._assistant_dialog.open()

    def select_assistant(self, name: str):
        """Select an AI assistant."""
        self.current_assistant = name
        if self._assistant_dialog:
            self._assistant_dialog.dismiss()

    def clear_chat(self):
        """Clear chat history."""
        self.chat_layout.clear_widgets()
        if self.current_assistant:
            assistant = self.app.assistant_manager.get_assistant(self.current_assistant)
            if assistant:
                assistant.clear_history()


class VoiceDebateApp(MDApp):
    """Main application class."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create data directory if it doesn't exist
        Path(config.data_dir).mkdir(parents=True, exist_ok=True)

        # Use global instances for now
        self.assistant_manager = assistant_manager
        self.speech_processor = speech_processor

        # Generate unique instance ID
        self.instance_id = str(uuid.uuid4())
        self.title = f"VoiceDebate - {self.instance_id[:8]}"

        self.theme_cls.theme_style = config.theme.theme_style
        self.theme_cls.primary_palette = config.theme.primary_palette
        self.theme_cls.accent_palette = config.theme.accent_palette

        # Load KV string
        Builder.load_string(KV)

        # Add custom colors
        for name, value in config.theme.colors.items():
            self.theme_cls.colors[name] = value

    def build(self):
        """Build and return the application's root widget."""
        # Set window size and position randomly to avoid overlap
        Window.size = (1024, 1200)
        Window.left = random.randint(0, 200)
        Window.top = random.randint(0, 100)

        screen = DebateScreen()
        screen.app = self  # Give screen access to app instance
        return screen

    def on_start(self):
        """Called when the application starts."""
        pass

    def schedule_async(self, coro):
        """Schedule an async coroutine to run in the event loop."""
        asyncio.get_event_loop().create_task(coro)

    def on_stop(self):
        """Called when the application is closing."""
        # Clean up instance-specific resources
        temp_path = Path(config.data_dir) / f"temp_audio_{self.instance_id}.wav"
        if temp_path.exists():
            temp_path.unlink()

        # Clean up any ongoing recording
        if hasattr(self.root, "_recording") and self.root._recording:
            asyncio.create_task(self.root.toggle_recording())

        # Clean up speech processor resources
        if self.speech_processor.microphone:
            self.speech_processor.microphone.finish()
        if self.speech_processor.dg_connection:
            self.speech_processor.dg_connection.finish()

        return True


def run():
    """Run the application."""
    # Set up asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Create and run the app
    app = VoiceDebateApp()

    # Run the app with asyncio support
    async def run_app():
        await app.async_run(async_lib="asyncio")

    loop.run_until_complete(run_app())
