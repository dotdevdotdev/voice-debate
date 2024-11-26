"""AI Assistant management for VoiceDebate."""

import asyncio
import logging
from typing import Optional
import anthropic
import openai
from .config import config
from .models import AssistantConfig

logger = logging.getLogger(__name__)

# Configure API clients
claude = anthropic.Anthropic(api_key=config.api.anthropic_api_key)
openai.api_key = config.api.openai_api_key


class Assistant:
    """AI Assistant handler."""

    def __init__(self, assistant_config: AssistantConfig):
        self.config = assistant_config
        self.conversation_history = []

    async def generate_response(self, user_input: str) -> str:
        """Generate a response from the AI assistant."""
        try:
            if self.config.provider == "claude":
                return await self._generate_claude_response(user_input)
            else:
                return await self._generate_gpt_response(user_input)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return (
                "I apologize, but I encountered an error while processing your input."
            )

    async def _generate_claude_response(self, user_input: str) -> str:
        """Generate response using Claude."""
        try:
            # Prepare messages - system prompt goes in system parameter, not in messages
            messages = []

            # Add conversation history
            for msg in self.conversation_history[
                -5:
            ]:  # Keep last 5 messages for context
                messages.append(msg)

            # Wrap the user input with context
            wrapped_input = (
                "Below is a transcription of what the user said. Since this is from voice "
                "recognition, some words might be missing or the thought might seem incomplete. "
                "Please respond naturally as if we're having a conversation - feel free to ask "
                "clarifying questions if needed. Keep responses concise and conversational.\n\n"
                f"TRANSCRIPTION: {user_input}"
            )

            # Add wrapped user input
            messages.append({"role": "user", "content": wrapped_input})

            # Update system prompt to emphasize conversational nature
            system_prompt = (
                "You are roleplaying as a character defined below. You should respond naturally as if that character would speak.\n"
                "IMPORTANT: Never use any action descriptions, emotes, or roleplaying indicators like *smiles*, *nods*, /me, etc. Only output direct speech.\n"
                "- Use single short sentences with simple words\n"
                "- Keep responses to 1-2 sentences maximum\n"
                "- Use basic punctuation like periods and question marks\n"
                "- No text formatting (*bold*, _italic_, etc)\n"
                "- No special characters or complex formatting\n\n"
                f"CHARACTER: {self.config.name}\n"
                f"{self.config.system_prompt}\n\n"
            )

            # Generate response with correct API structure
            response = await asyncio.to_thread(
                claude.messages.create,
                model=self.config.model,
                system=system_prompt,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=1000,
            )

            # Update conversation history with original (unwrapped) input
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append(
                {"role": "assistant", "content": response.content[0].text}
            )

            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude error: {e}")
            raise

    async def _generate_gpt_response(self, user_input: str) -> str:
        """Generate response using GPT."""
        try:
            # Prepare conversation messages
            messages = []

            # Add system prompt
            messages.append({"role": "system", "content": self.config.system_prompt})

            # Add conversation history
            for msg in self.conversation_history[
                -5:
            ]:  # Keep last 5 messages for context
                messages.append(msg)

            # Add user input
            messages.append({"role": "user", "content": user_input})

            # Generate response
            response = await openai.ChatCompletion.acreate(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=1000,
            )

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GPT error: {e}")
            raise

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []


class AssistantManager:
    """Manager for multiple AI assistants."""

    def __init__(self):
        self.assistants: dict[str, Assistant] = {}
        self._load_default_assistants()

    def _load_default_assistants(self):
        """Load default assistant configurations."""
        default_configs = [
            AssistantConfig(
                name="Socrates",
                description="A philosophical debater who uses the Socratic method",
                system_prompt=(
                    "You are Socrates, the ancient Greek philosopher known for your method of "
                    "asking probing questions to stimulate critical thinking. Engage in debate "
                    "by questioning assumptions and helping others examine their beliefs.\n\n"
                ),
                provider="claude",
                model="claude-3-haiku-20240307",
                temperature=0.7,
                voice_id="ErXwobaYiN019PkySvjV",  # Antoni voice
                voice_stability=0.5,
                voice_clarity=0.75,
            ),
            AssistantConfig(
                name="Aristotle",
                description="A logical and analytical debater",
                system_prompt=(
                    "You are Aristotle, the ancient Greek philosopher known for systematic "
                    "logic and empirical observation. Engage in debate by analyzing arguments "
                    "carefully and drawing on evidence and reason.\n\n"
                ),
                provider="gpt",
                model="gpt-4",
                temperature=0.6,
                voice_id="VR6AewLTigWG4xSOukaG",  # Arnold voice
                voice_stability=0.6,
                voice_clarity=0.8,
            ),
        ]

        for config in default_configs:
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


# Global assistant manager instance
assistant_manager = AssistantManager()
