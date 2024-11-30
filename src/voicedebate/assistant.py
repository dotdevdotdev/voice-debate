"""AI Assistant management for VoiceDebate."""

import asyncio
import logging
from typing import Optional, Dict, Any
import anthropic
import openai
from .config import config
from .models import AssistantConfig
from .character_loader import load_character_configs
import random
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Configure API clients
claude = anthropic.Anthropic(api_key=config.api.anthropic_api_key)
openai.api_key = config.api.openai_api_key


class Assistant:
    """AI Assistant handler."""

    def __init__(self, assistant_config: AssistantConfig):
        self.config = assistant_config
        self.conversation_history = []
        self.character_data: Dict[str, Any] = {}  # Store the full character data
        self._load_character_data()

    def _load_character_data(self):
        """Load the full character data from JSON."""
        characters_dir = Path(__file__).parent / "data" / "characters"
        character_file = characters_dir / f"{self.config.name.lower()}.json"

        try:
            with open(character_file, "r", encoding="utf-8") as f:
                self.character_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading character data: {e}")

    def _should_use_scripted_response(self) -> bool:
        """Determine if we should use a scripted response (20% chance)."""
        return random.random() < 0.2

    def _should_use_response_starter(self) -> bool:
        """Determine if we should use a response starter (40% chance)."""
        return random.random() < 0.4

    def _get_random_scripted_response(self) -> Optional[str]:
        """Get a random scripted response based on context."""
        try:
            scripted_responses = self.character_data["character_definition"][
                "speech_style"
            ]["scripted_responses"]
            category = random.choice(list(scripted_responses.keys()))
            return random.choice(scripted_responses[category])
        except (KeyError, IndexError):
            return None

    def _get_random_response_starter(self) -> Optional[str]:
        """Get a random response starter."""
        try:
            starters = self.character_data["character_definition"]["speech_style"][
                "response_starters"
            ]
            return random.choice(starters)
        except (KeyError, IndexError):
            return None

    async def generate_response(self, user_input: str) -> str:
        """Generate a response from the AI assistant."""
        try:
            # Create message for current input
            current_message = {"role": "user", "content": user_input}

            if self.config.provider == "claude":
                # Get response before adding to history to avoid including it in the request
                response = await self._generate_claude_response(current_message)
            else:
                response = await self._generate_gpt_response(current_message)

            # Add messages to history after getting response
            self.conversation_history.append(current_message)
            self.conversation_history.append({"role": "assistant", "content": response})

            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_msg = (
                "I apologize, but I encountered an error while processing your input."
            )
            self.conversation_history.append(
                {"role": "assistant", "content": error_msg}
            )
            return error_msg

    def get_conversation_history(self) -> list[dict]:
        """Get the full conversation history."""
        return self.conversation_history

    def get_last_n_messages(self, n: int = 5) -> list[dict]:
        """Get the last N messages from conversation history."""
        return self.conversation_history[-n:] if self.conversation_history else []

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    async def _generate_claude_response(self, current_message: dict) -> str:
        """Generate response using Claude."""
        try:
            messages = self.conversation_history + [current_message]

            # Decide whether to use a scripted response
            if self._should_use_scripted_response():
                scripted = self._get_random_scripted_response()
                if scripted:
                    return scripted

            # Decide whether to use a response starter
            starter = None
            if self._should_use_response_starter():
                starter = self._get_random_response_starter()

            # Generate response using conversation history and system prompt
            response = await asyncio.to_thread(
                claude.messages.create,
                model=self.config.model,
                system=self.config.system_prompt,
                messages=[
                    *messages,
                    *([{"role": "assistant", "content": starter}] if starter else []),
                ],
                temperature=self.config.temperature,
                max_tokens=1000,
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Claude error: {e}")
            raise

    async def _generate_gpt_response(self, current_message: dict) -> str:
        """Generate response using GPT."""
        try:
            # Convert Anthropic format to OpenAI format
            messages = [{"role": "system", "content": self.config.system_prompt}]

            # Add conversation history and current message
            for msg in self.conversation_history + [current_message]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            response = await openai.ChatCompletion.acreate(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=1000,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"GPT error: {e}")
            raise


class AssistantManager:
    """Manager for multiple AI assistants."""

    def __init__(self):
        self.assistants: dict[str, Assistant] = {}
        self._load_default_assistants()

    def _load_default_assistants(self):
        """Load assistant configurations from JSON files."""
        configs = load_character_configs()
        for config in configs:
            self.add_assistant(config)

    def add_assistant(self, config: AssistantConfig):
        """Add a new assistant."""
        self.assistants[config.name] = Assistant(config)

    def get_assistant(self, name: str) -> Optional[Assistant]:
        """Get an assistant by name."""
        return self.assistants.get(name)

    def list_assistants(self) -> list[str]:
        """List all available assistants."""
        return list(self.assistants.keys())

    def remove_assistant(self, name: str):
        """Remove an assistant."""
        if name in self.assistants:
            del self.assistants[name]


# Create global instance
assistant_manager = AssistantManager()
