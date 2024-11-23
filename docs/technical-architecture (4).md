[Previous sections through Project Structure remain unchanged]

## Debate Configuration System

### Assistant Configuration
```python
from dataclasses import dataclass
from typing import Dict, Optional
from pydantic import BaseSettings

@dataclass
class AssistantConfig:
    # Identification
    name: str
    description: Optional[str] = None
    
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
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "voice_id": self.voice_id,
            "voice_stability": self.voice_stability,
            "voice_clarity": self.voice_clarity,
            "voice_style": self.voice_style
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AssistantConfig':
        return cls(**data)
```

### Assistant Manager
```python
import os
import yaml
from pathlib import Path
from typing import Dict, List

class AssistantManager:
    def __init__(self):
        self.config_dir = Path.home() / ".voicedebate" / "assistants"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.current_assistant: Optional[AssistantConfig] = None
        self.assistants: Dict[str, AssistantConfig] = {}
        self.load_assistants()
    
    def load_assistants(self) -> None:
        """Load all assistant configurations from YAML files"""
        for config_file in self.config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r') as f:
                    data = yaml.safe_load(f)
                    assistant = AssistantConfig.from_dict(data)
                    self.assistants[assistant.name] = assistant
            except Exception as e:
                print(f"Error loading assistant {config_file}: {e}")
    
    def save_assistant(self, assistant: AssistantConfig) -> None:
        """Save assistant configuration to YAML file"""
        file_path = self.config_dir / f"{assistant.name}.yaml"
        with open(file_path, 'w') as f:
            yaml.safe_dump(assistant.to_dict(), f)
        self.assistants[assistant.name] = assistant
    
    def delete_assistant(self, name: str) -> None:
        """Delete assistant configuration"""
        if name in self.assistants:
            file_path = self.config_dir / f"{name}.yaml"
            file_path.unlink(missing_ok=True)
            del self.assistants[name]
    
    def get_assistant_names(self) -> List[str]:
        """Get list of available assistants"""
        return list(self.assistants.keys())
    
    def set_current_assistant(self, name: str) -> None:
        """Set the current active assistant"""
        if name in self.assistants:
            self.current_assistant = self.assistants[name]
```

### Main Application UI
```kv
<MainScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            title: "VoiceDebate"
            right_action_items: [["account-plus", lambda x: root.show_assistant_creator()]]
        
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: 0.9
            
            # Assistant Selection Panel
            MDCard:
                size_hint_x: 0.3
                padding: "16dp"
                
                MDBoxLayout:
                    orientation: 'vertical'
                    
                    MDLabel:
                        text: "Debate Assistants"
                        bold: True
                    
                    ScrollView:
                        MDList:
                            id: assistant_list
                    
                    MDFillRoundFlatButton:
                        text: "Add to Chat"
                        on_press: root.add_assistant_to_chat()
                        disabled: not root.selected_assistant
            
            # Chat Area
            MDCard:
                size_hint_x: 0.7
                padding: "16dp"
                
                MDBoxLayout:
                    orientation: 'vertical'
                    
                    ScrollView:
                        MDList:
                            id: chat_messages
                    
                    MDBoxLayout:
                        size_hint_y: 0.1
                        spacing: "8dp"
                        
                        MDFillRoundFlatIconButton:
                            text: "Start"
                            icon: "microphone"
                            on_press: root.start_recording()
```

### Assistant Creation/Edit Dialog
```kv
<AssistantDialog>:
    MDBoxLayout:
        orientation: 'vertical'
        padding: "16dp"
        spacing: "8dp"
        
        MDTextField:
            id: name
            hint_text: "Assistant Name"
            helper_text: "Give your debate assistant a name"
            
        MDTextField:
            id: description
            hint_text: "Description (optional)"
            multiline: True
            
        MDTextField:
            id: system_prompt
            hint_text: "System Prompt"
            multiline: True
            helper_text: "Define your assistant's personality and debate style"
            
        MDBoxLayout:
            orientation: 'horizontal'
            spacing: "8dp"
            
            MDSegmentedButton:
                id: provider_select
                MDSegmentedButtonItem:
                    text: "Claude"
                MDSegmentedButtonItem:
                    text: "GPT"
            
            MDDropDownItem:
                id: model_select
                text: "Select Model"
        
        MDExpansionPanel:
            title: "Voice Settings"
            content: VoiceSettings()

        MDExpansionPanel:
            title: "Advanced Settings"
            content: AdvancedSettings()
        
        MDFillRoundFlatButton:
            text: "Save Assistant"
            on_press: root.save_assistant()
```

### Main Screen Implementation
```python
class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assistant_manager = AssistantManager()
        self.selected_assistant = None
        self.load_assistants()
    
    def load_assistants(self):
        """Load assistant list into UI"""
        assistant_list = self.ids.assistant_list
        assistant_list.clear_widgets()
        
        for name in self.assistant_manager.get_assistant_names():
            item = AssistantListItem(text=name)
            item.bind(on_release=self.select_assistant)
            assistant_list.add_widget(item)
    
    def select_assistant(self, item):
        """Handle assistant selection"""
        self.selected_assistant = item.text
        self.assistant_manager.set_current_assistant(item.text)
    
    def add_assistant_to_chat(self):
        """Add selected assistant to the chat"""
        if self.selected_assistant:
            # Initialize AI and voice settings
            # Start the debate session
            pass
    
    def show_assistant_creator(self):
        """Show assistant creation dialog"""
        dialog = AssistantDialog()
        dialog.open()
```

[Previous sections remain unchanged...]
