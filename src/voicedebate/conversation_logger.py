"""Conversation logging module for VoiceDebate."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from .config import config

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""

    timestamp: str
    speaker: str  # "User" or assistant name + model (e.g., "Socrates (Claude-3)")
    message: str


@dataclass
class Conversation:
    """Full conversation record."""

    id: str
    character_name: str
    turns: List[ConversationTurn]


class ConversationLogger:
    """Handles logging of conversations for analysis."""

    def __init__(self):
        self.logs_dir = Path(config.data_dir) / "conversation_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.current_conversation: Optional[Conversation] = None

    def start_conversation(self, character_name: str) -> str:
        """Start a new conversation."""
        try:
            if self.current_conversation:
                self.end_conversation()

            conversation_id = (
                f"{character_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            logger.info(f"Starting new conversation: {conversation_id}")

            self.current_conversation = Conversation(
                id=conversation_id, character_name=character_name, turns=[]
            )
            self._save_conversation()
            return conversation_id
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            raise

    def log_turn(self, speaker: str, message: str, model: Optional[str] = None):
        """Log a single conversation turn."""
        if not self.current_conversation:
            logger.warning("No active conversation to log turn")
            return

        try:
            # Format speaker name for AI responses
            if model and speaker != "User":
                speaker = f"{speaker} ({model})"

            turn = ConversationTurn(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                speaker=speaker,
                message=message,
            )
            self.current_conversation.turns.append(turn)
            self._save_conversation()
        except Exception as e:
            logger.error(f"Error logging turn: {e}")

    def end_conversation(self):
        """End the current conversation."""
        if self.current_conversation:
            self._save_conversation()
            self.current_conversation = None

    def _save_conversation(self):
        """Save the current conversation to file."""
        if not self.current_conversation:
            logger.warning("Attempted to save conversation but no active conversation")
            return

        file_path = self.logs_dir / f"{self.current_conversation.id}.json"
        try:
            conversation_dict = asdict(self.current_conversation)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(conversation_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved conversation to: {file_path}")
            logger.debug(f"Conversation content: {conversation_dict}")
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")


# Global instance
conversation_logger = ConversationLogger()
