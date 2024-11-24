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
from voicedebate.speech import speech_processor
from voicedebate.assistant import assistant_manager

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
    
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: get_color_from_hex(app.theme_cls.colors['background'])
        padding: "32dp"
        spacing: "16dp"
        
        MDBoxLayout:
            size_hint_y: None
            height: "160dp"
            spacing: "16dp"
            
            MDIconButton:
                icon: "account-switch"
                on_release: root.show_assistant_dialog()
                icon_size: "96dp"
                size_hint: None, None
                size: "160dp", "160dp"
            
            Widget:
                size_hint_x: 1
            
            MDLabel:
                text: root.current_assistant or "Select Assistant"
                theme_text_color: "Primary"
            
            MDIconButton:
                icon: "delete"
                on_release: root.clear_chat()
        
        MDScrollView:
            do_scroll_x: False
            
            MDList:
                id: chat_layout
                spacing: "16dp"
                padding: "16dp"
        
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

MDScreen:
    MDBoxLayout:
        orientation: "vertical"
        spacing: "48dp"
        padding: "48dp"
        
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
                text: root.current_assistant or "Select Assistant"
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
        
        # Main content
        MDLabel:
            text: "VoiceDebate"
            halign: "center"
            font_style: "H2"
            size_hint_y: None
            height: self.texture_size[1]
            padding_y: "48dp"
        
        Widget:
            size_hint_y: 0.2
        
        MDBoxLayout:
            orientation: "vertical"
            spacing: "48dp"
            adaptive_height: True
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            
            MDRaisedButton:
                id: assistant_button
                text: "Select Assistant"
                font_size: "48sp"
                size_hint: (None, None)
                size: "600dp", "160dp"
                pos_hint: {"center_x": 0.5}
                on_release: app.root.show_assistant_dialog()
                md_bg_color: app.theme_cls.primary_color
            
            MDRaisedButton:
                id: record_button
                text: "Start Recording"
                font_size: "48sp"
                size_hint: (None, None)
                size: "600dp", "160dp"
                pos_hint: {"center_x": 0.5}
                on_release: app.schedule_async(root.toggle_recording())
                md_bg_color: app.theme_cls.accent_color
"""

class MessageCard(MDCard):
    """Card widget for displaying chat messages."""
    speaker = StringProperty()
    message = StringProperty()

class DebateScreen(MDScreen):
    """Main debate screen."""
    
    chat_layout = ObjectProperty(None)
    current_assistant: Optional[str] = None
    _recording = False
    _assistant_dialog = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._temp_audio_path = Path(config.data_dir) / "temp_audio.wav"
    
    def add_message(self, speaker: str, message: str):
        """Add a message to the chat."""
        card = MessageCard(
            speaker=speaker,
            message=message
        )
        self.chat_layout.add_widget(card)
        
        # Scroll to bottom
        def scroll_bottom(*args):
            scroll_view = self.chat_layout.parent
            scroll_view.scroll_y = 0
        Clock.schedule_once(scroll_bottom, 0.1)
    
    async def toggle_recording(self):
        """Toggle audio recording state."""
        try:
            if not self._recording:
                logger.info("Starting recording...")
                await speech_processor.start_capture()
                self._recording = True
                self.ids.record_button.text = "Stop Recording"
                self.ids.record_button.md_bg_color = self.theme_cls.colors['secondary']
            else:
                logger.info("Stopping recording...")
                audio_data, transcription = await speech_processor.stop_capture()
                self._recording = False
                self.ids.record_button.text = "Start Recording"
                self.ids.record_button.md_bg_color = self.theme_cls.colors['primary']
                
                if transcription["text"]:
                    # Add user message
                    self.add_message("You", transcription["text"])
                    
                    # Get AI response
                    assistant = assistant_manager.get_assistant(self.current_assistant)
                    if assistant:
                        response_text = await assistant.generate_response(transcription["text"])
                        self.add_message(self.current_assistant, response_text)
                        
                        # Synthesize and play response
                        audio = await speech_processor.synthesize_speech(
                            text=response_text,
                            voice_id=assistant.config.voice_id,
                            stability=assistant.config.voice_stability,
                            clarity=assistant.config.voice_clarity,
                            style=assistant.config.voice_style
                        )
                        
                        if audio:
                            # Save audio to temporary file
                            self._temp_audio_path.write_bytes(audio)
                            
                            # Play audio
                            sound = SoundLoader.load(str(self._temp_audio_path))
                            if sound:
                                sound.play()
        except Exception as e:
            logger.error(f"Error in recording toggle: {e}")
            self._recording = False
    
    def show_assistant_dialog(self):
        """Show dialog to select AI assistant."""
        if not self._assistant_dialog:
            items = []
            for name in assistant_manager.list_assistants():
                item = OneLineIconListItem(
                    text=name.title(),
                    font_style="H3",
                    text_color=self.theme_cls.primary_color,
                    on_release=lambda x, n=name: self.select_assistant(n),
                    _height="120dp",
                    divider="Full",
                    divider_color=self.theme_cls.primary_color
                )
                items.append(item)
            
            self._assistant_dialog = MDDialog(
                title="Select AI Assistant",
                title_font_size="64sp",
                type="simple",
                items=items,
                size_hint=(0.9, 0.9),
                md_bg_color=self.theme_cls.bg_dark,
                radius=[20, 20, 20, 20],
                elevation=10
            )
        
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
            assistant = assistant_manager.get_assistant(self.current_assistant)
            if assistant:
                assistant.clear_history()

class VoiceDebateApp(MDApp):
    """Main application class."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "VoiceDebate"
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
        return DebateScreen()
    
    def on_start(self):
        """Called when the application starts."""
        pass
    
    def schedule_async(self, coro):
        """Schedule an async coroutine to run in the event loop."""
        asyncio.get_event_loop().create_task(coro)

def run():
    """Run the application."""
    # Set up asyncio event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Create and run the app
    app = VoiceDebateApp()
    
    # Run the app with asyncio support
    async def run_app():
        await app.async_run(async_lib='asyncio')
    
    loop.run_until_complete(run_app())