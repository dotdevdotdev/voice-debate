[Previous sections through Project Structure remain the same, adding new sections...]

## Default Assistant Templates

### YAML Configuration Format
```yaml
# ~/.voicedebate/assistants/socratic_teacher.yaml
name: "Socratic Teacher"
description: "A philosophical debate partner who uses the Socratic method"
system_prompt: |
  You are a skilled teacher who uses the Socratic method in debates.
  Always respond with questions that challenge assumptions and probe deeper understanding.
  Keep responses concise and focused on one key point at a time.
provider: "claude"
model: "claude-3-haiku-20240307"
temperature: 0.7
voice_id: "21m00Tcm4TlvDq8ikWAM"
voice_stability: 0.5
voice_clarity: 0.75
voice_style: 0.0

# ~/.voicedebate/assistants/devil_advocate.yaml
name: "Devil's Advocate"
description: "A challenger who takes the opposing view in any debate"
system_prompt: |
  You are a skilled debater who always takes the opposing viewpoint.
  Challenge every assertion with well-reasoned counterarguments.
  Maintain a respectful but persistent tone.
provider: "gpt"
model: "gpt-4-0125-preview"
temperature: 0.8
voice_id: "wViXBPUzp2ZZixB1xQuM"
voice_stability: 0.7
voice_clarity: 0.8
voice_style: 0.2
```

## UI Theme Configuration
```python
# config/theme.py
THEME_COLORS = {
    'background': '#000000',  # Solid black
    'primary': '#39FF14',     # Neon green
    'secondary': '#00BFFF',   # Neon blue
    'surface': '#111111',     # Slightly lighter black for cards
    'text_primary': '#39FF14',
    'text_secondary': '#00BFFF',
}

# Apply theme to KivyMD
class VoiceDebateTheme:
    @staticmethod
    def apply():
        from kivymd.theming import ThemeManager
        theme = ThemeManager()
        theme.theme_style = "Dark"
        theme.primary_palette = "Green"
        theme.accent_palette = "Blue"
```

### Custom Widget Styles
```kv
<MDCard>:
    md_bg_color: app.theme_cls.get_color('surface')
    line_color: app.theme_cls.get_color('secondary')

<MDLabel>:
    theme_text_color: "Custom"
    text_color: app.theme_cls.get_color('primary')

<MDFillRoundFlatIconButton>:
    md_bg_color: app.theme_cls.get_color('surface')
    text_color: app.theme_cls.get_color('primary')
    icon_color: app.theme_cls.get_color('primary')
    line_color: app.theme_cls.get_color('secondary')
```

## Enhanced Chat Interface
```kv
<ChatMessage>:
    orientation: 'vertical'
    padding: "8dp"
    spacing: "4dp"
    
    canvas.before:
        Color:
            rgba: app.theme_cls.get_color('surface')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15, 15, 15, 15]
    
    MDLabel:
        text: root.speaker_name
        font_style: "Caption"
        size_hint_y: None
        height: self.texture_size[1]
        theme_text_color: "Custom"
        text_color: app.theme_cls.get_color('secondary')
    
    MDLabel:
        text: root.message_text
        theme_text_color: "Custom"
        text_color: app.theme_cls.get_color('primary')

<ChatArea>:
    BoxLayout:
        orientation: 'vertical'
        
        ScrollView:
            MDList:
                id: messages
                padding: "8dp"
                spacing: "8dp"
        
        MDCard:
            size_hint_y: None
            height: "60dp"
            padding: "8dp"
            
            MDIconButton:
                icon: "microphone"
                theme_text_color: "Custom"
                text_color: app.theme_cls.get_color('primary')
                on_press: root.toggle_recording()
            
            MDLabel:
                text: root.status_text
                theme_text_color: "Custom"
                text_color: app.theme_cls.get_color('secondary')
```

## Example Default Assistant
```python
DEFAULT_ASSISTANT = {
    "name": "Basic Debater",
    "description": "A balanced debate partner for general discussions",
    "system_prompt": """You are a balanced debate partner who engages in thoughtful discussion.
    Your responses should:
    1. Be concise (2-3 sentences)
    2. Focus on one key point at a time
    3. Ask follow-up questions
    4. Remain neutral and analytical
    5. Encourage deeper exploration of topics""",
    "provider": "claude",
    "model": "claude-3-haiku-20240307",
    "temperature": 0.7,
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "voice_stability": 0.5,
    "voice_clarity": 0.75,
    "voice_style": 0.0
}

def create_default_assistant():
    """Create default assistant if no assistants exist"""
    assistant_manager = AssistantManager()
    if not assistant_manager.get_assistant_names():
        assistant = AssistantConfig.from_dict(DEFAULT_ASSISTANT)
        assistant_manager.save_assistant(assistant)
        return assistant
```

[Previous sections remain unchanged...]
