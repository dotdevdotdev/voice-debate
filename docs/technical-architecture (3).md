[Previous sections remain unchanged through Project Structure, adding new section after UI Components...]

## Debate Configuration System

### Settings Management
```python
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class DebateConfig:
    # LLM Settings
    system_prompt: str
    provider: str = "claude"  # "claude" or "gpt"
    model: str = "claude-3-haiku-20240307"
    temperature: float = 0.7
    
    # Voice Settings
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    voice_stability: float = 0.5
    voice_clarity: float = 0.75
    voice_style: float = 0.0
    
    # Debate Settings
    response_max_tokens: int = 150
    debate_style: str = "conversational"  # conversational, formal, socratic
    
    def to_dict(self) -> Dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            # ... other settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DebateConfig':
        return cls(**data)
```

### Settings UI Components
```kv
<SettingsScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            title: "Debate Configuration"
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
        
        MDTabs:
            Tab:
                title: "LLM Settings"
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    
                    MDTextField:
                        id: system_prompt
                        multiline: True
                        hint_text: "System Prompt"
                        helper_text: "Define your debate opponent's personality and style"
                        helper_text_mode: "persistent"
                    
                    MDSegmentedButton:
                        id: provider_select
                        MDSegmentedButtonItem:
                            text: "Claude"
                        MDSegmentedButtonItem:
                            text: "GPT"
                    
                    MDDropDownItem:
                        id: model_select
                        text: "Select Model"
                    
                    MDSlider:
                        id: temperature
                        min: 0
                        max: 1
                        value: 0.7
                        hint: "Temperature"
            
            Tab:
                title: "Voice Settings"
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    
                    MDDropDownItem:
                        id: voice_select
                        text: "Select Voice"
                    
                    MDSlider:
                        id: stability
                        min: 0
                        max: 1
                        value: 0.5
                        hint: "Stability"
                    
                    MDSlider:
                        id: clarity
                        min: 0
                        max: 1
                        value: 0.75
                        hint: "Clarity"
                        
                    MDSlider:
                        id: style
                        min: 0
                        max: 1
                        value: 0
                        hint: "Style"

            Tab:
                title: "Debate Settings"
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: "16dp"
                    spacing: "8dp"
                    
                    MDTextField:
                        id: max_tokens
                        hint_text: "Max Response Tokens"
                        helper_text: "Maximum length of AI responses"
                        input_filter: "int"
                    
                    MDSegmentedButton:
                        id: debate_style
                        MDSegmentedButtonItem:
                            text: "Conversational"
                        MDSegmentedButtonItem:
                            text: "Formal"
                        MDSegmentedButtonItem:
                            text: "Socratic"
```

### Settings Manager Class
```python
class SettingsManager:
    def __init__(self):
        self.config = DebateConfig()
        self.config_file = "debate_config.json"
        
    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.config = DebateConfig.from_dict(data)
        except FileNotFoundError:
            self.save_config()  # Save default config
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
    
    def update_config(self, **kwargs) -> None:
        """Update configuration with new values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()
```

### Settings Screen Implementation
```python
class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings_manager = SettingsManager()
        self.load_settings()
    
    def load_settings(self):
        """Load current settings into UI"""
        config = self.settings_manager.config
        self.ids.system_prompt.text = config.system_prompt
        self.ids.provider_select.selected = config.provider
        self.update_model_options(config.provider)
        # ... load other settings
    
    def update_model_options(self, provider: str):
        """Update available models based on provider"""
        models = {
            "claude": ["claude-3-haiku-20240307"],
            "gpt": ["gpt-4-0125-preview"]
        }
        self.ids.model_select.items = models.get(provider, [])
    
    def save_settings(self):
        """Save settings from UI to config"""
        self.settings_manager.update_config(
            system_prompt=self.ids.system_prompt.text,
            provider=self.ids.provider_select.selected,
            model=self.ids.model_select.text,
            temperature=self.ids.temperature.value,
            # ... other settings
        )
```

[Previous sections remain unchanged...]

