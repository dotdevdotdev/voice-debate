# VoiceDebate Technical Architecture Document

## Project Structure
```
voicedebate/
├── main.py               # Application entry point
├── config/
│   ├── __init__.py
│   └── settings.py       # Configuration and API keys
├── audio/
│   ├── __init__.py
│   ├── manager.py        # AudioManager implementation
│   ├── buffer.py         # BufferManager implementation
│   └── devices.py        # Audio device handling
├── services/
│   ├── __init__.py
│   ├── speech.py         # Speech services (Deepgram, ElevenLabs)
│   └── ai.py             # AI service integration
├── ui/
│   ├── __init__.py
│   ├── debate.kv         # Main UI layout
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── debate_area.py     # Debate display widget
│   │   ├── audio_controls.py  # Audio control widget
│   │   └── status_bar.py      # Status display widget
│   └── screens/
│       ├── __init__.py
│       └── main_screen.py     # Main application screen
└── utils/
    ├── __init__.py
    └── events.py         # Event definitions
```

## Event System

### Core Events
```python
class VoiceDebateEvents:
    # Audio Events
    ON_RECORDING_START = 'on_recording_start'
    ON_RECORDING_STOP = 'on_recording_stop'
    ON_AUDIO_ERROR = 'on_audio_error'
    
    # Speech Service Events
    ON_TRANSCRIPTION_UPDATE = 'on_transcription_update'
    ON_TRANSCRIPTION_COMPLETE = 'on_transcription_complete'
    ON_SPEECH_GENERATION_START = 'on_speech_generation_start'
    ON_SPEECH_GENERATION_COMPLETE = 'on_speech_generation_complete'
    
    # AI Service Events
    ON_AI_RESPONSE_START = 'on_ai_response_start'
    ON_AI_RESPONSE_COMPLETE = 'on_ai_response_complete'
    ON_AI_ERROR = 'on_ai_error'
    
    # UI Events
    ON_DEBATE_START = 'on_debate_start'
    ON_DEBATE_STOP = 'on_debate_stop'
    ON_SETTINGS_CHANGE = 'on_settings_change'
```

### Event Usage Example
```python
from kivy.event import EventDispatcher

class AudioManager(EventDispatcher):
    def __init__(self):
        self.register_event_type(VoiceDebateEvents.ON_RECORDING_START)
        self.register_event_type(VoiceDebateEvents.ON_RECORDING_STOP)
        
    def start_capture(self):
        # Start audio capture
        self.dispatch(VoiceDebateEvents.ON_RECORDING_START)
```

## Recommended UI Components

### Modern Kivy Widgets
1. **MDCard** (from KivyMD) for main content areas:
```kv
<DebateArea>:
    MDCard:
        elevation: 1
        padding: "8dp"
        radius: [15, 15, 15, 15]
```

2. **MDTopAppBar** for header:
```kv
<DebateHeader>:
    MDTopAppBar:
        title: "VoiceDebate"
        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
        elevation: 0
```

3. **MDFillRoundFlatIconButton** for controls:
```kv
<AudioControls>:
    MDFillRoundFlatIconButton:
        text: "Start Debate"
        icon: "microphone"
        on_press: root.start_debate()
```

### Main Layout Structure
```kv
<MainScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        
        DebateHeader:
            size_hint_y: 0.1
        
        DebateArea:
            size_hint_y: 0.7
            
            MDCard:
                # Debate content area
                orientation: 'vertical'
                padding: "16dp"
                spacing: "12dp"
                
                MDLabel:
                    text: "Debate Transcript"
                    bold: True
                
                ScrollView:
                    MDList:
                        id: debate_messages
        
        AudioControls:
            size_hint_y: 0.2
            
            MDFloatLayout:
                MDFillRoundFlatIconButton:
                    text: "Start"
                    icon: "microphone"
                    pos_hint: {'center_x': .5, 'center_y': .5}
```

## Core Components

[Previous AudioManager, BufferManager, and SpeechServicesManager classes remain the same]

## Audio System Selection
The system will start with Audiostream for these reasons:
1. Better control over buffer management
2. More predictable cross-platform behavior
3. Direct access to audio stream data for real-time processing
4. Better integration with Deepgram's streaming API

## Implementation Sequence

1. **Phase 1: Core Setup and Testing**
   - Create project structure
   - Implement basic event system
   - Test audio capture/playback
   - Create minimal UI for testing

2. **Phase 2: Service Integration**
   - Implement Deepgram streaming
   - Add ElevenLabs synthesis
   - Basic AI service integration
   - Event handling for services

3. **Phase 3: UI Development**
   - Complete debate interface
   - Add audio visualization
   - Implement settings screen
   - Add error handling and user feedback

## Resource Management

[Previous resource management section remains the same]

## Next Steps

1. Create project structure
2. Implement basic event system
3. Create minimal UI with KivyMD components
4. Test audio capture pipeline

The LLM can modify these specifications as needed while maintaining the core architecture and event system. The key is ensuring proper event handling and maintaining a clean separation of concerns between audio processing, services, and UI components.

Would you like me to elaborate on any of these components or provide more specific implementation details for any section?
