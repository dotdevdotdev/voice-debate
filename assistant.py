"""AI Assistant management for VoiceDebate."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List
import anthropic
import openai
from .config import config
from .models import AssistantConfig

logger = logging.getLogger(__name__)

class AssistantManager:
    """Manages AI assistant configurations and interactions."""
    
    def __init__(self):
        self.assistants_dir = config.data_dir / "assistants"
        self.assistants_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, AssistantConfig] = {}
        self._load_assistants()
    
    def _load_assistants(self):
        """Load assistant configurations from disk."""
        for file in self.assistants_dir.glob("*.json"):
            try:
                config_data = json.loads(file.read_text())
                assistant = AssistantConfig(**config_data)
                self._cache[assistant.name] = assistant
            except Exception as e:
                logger.error(f"Failed to load assistant config {file}: {e}")
    
    def save_assistant(self, assistant: AssistantConfig):
        """Save assistant configuration to disk."""
        file_path = self.assistants_dir / f"{assistant.name.lower().replace(' ', '_')}.json"
        file_path.write_text(assistant.model_dump_json(indent=2))
        self._cache[assistant.name] = assistant
    
    def get_assistant(self, name: str) -> Optional[AssistantConfig]:
        """Get assistant configuration by name."""
        return self._cache.get(name)
    
    def get_assistant_names(self) -> List[str]:
        """Get list of available assistant names."""
        return list(self._cache.keys())
    
    def create_default_assistants(self):
        """Create default assistant configurations."""
        defaults = [
            AssistantConfig(
                name="Socratic Teacher",
                description="A philosophical debate partner who uses the Socratic method",
                system_prompt="""You are a skilled teacher who uses the Socratic method in debates.
                Always respond with questions that challenge assumptions and probe deeper understanding.
                Keep responses concise and focused on one key point at a time.""",
                provider="claude",
                model="claude-3-haiku-20240307",
                temperature=0.7,
                voice_id="21m00Tcm4TlvDq8ikWAM",
                voice_stability=0.5,
                voice_clarity=0.75,
                voice_style=0.0
            ),
            AssistantConfig(
                name="Devil's Advocate",
                description="A challenger who takes the opposing view in any debate",
                system_prompt="""You are a skilled debater who always takes the opposing viewpoint.
                Challenge every assertion with well-reasoned counterarguments.
                Maintain a respectful but persistent tone.""",
                provider="gpt",
                model="gpt-4-0125-preview",
                temperature=0.8,
                voice_id="wViXBPUzp2ZZixB1xQuM",
                voice_stability=0.7,
                voice_clarity=0.8,
                voice_style=0.2
            )
        ]
        
        for assistant in defaults:
            self.save_assistant(assistant)

class AIClient:
    """Client for interacting with AI models."""
    
    def __init__(self, assistant: AssistantConfig):
        self.assistant = assistant
        self.conversation_history = []
        
        if assistant.provider == "claude":
            self.client = anthropic.Anthropic(api_key=config.api.anthropic_api_key)
        else:
            self.client = openai.Client(api_key=config.api.openai_api_key)
    
    async def get_response(self, message: str) -> str:
        """Get AI response to user message."""
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            if self.assistant.provider == "claude":
                response = await self._get_claude_response(message)
            else:
                response = await self._get_gpt_response(message)
            
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            raise
    
    async def _get_claude_response(self, message: str) -> str:
        """Get response from Claude."""
        messages = [{"role": "system", "content": self.assistant.system_prompt}]
        messages.extend(self.conversation_history)
        
        response = await self.client.messages.create(
            model=self.assistant.model,
            messages=messages,
            max_tokens=1024,
            temperature=self.assistant.temperature
        )
        
        return response.content[0].text
    
    async def _get_gpt_response(self, message: str) -> str:
        """Get response from GPT."""
        messages = [{"role": "system", "content": self.assistant.system_prompt}]
        messages.extend(self.conversation_history)
        
        response = await self.client.chat.completions.create(
            model=self.assistant.model,
            messages=messages,
            max_tokens=1024,
            temperature=self.assistant.temperature
        )
        
        return response.choices[0].message.content
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
