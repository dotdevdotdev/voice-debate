"""Character configuration loader for VoiceDebate."""

import json
import logging
from pathlib import Path
from typing import Dict, List
from .models import AssistantConfig

logger = logging.getLogger(__name__)


def load_character_configs() -> List[AssistantConfig]:
    """Load all character configurations from JSON files."""
    characters_dir = Path(__file__).parent / "data" / "characters"
    configs = []

    try:
        for json_file in characters_dir.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Convert JSON data to AssistantConfig
                config = AssistantConfig(
                    name=data["name"],
                    description=data["description"],
                    system_prompt=_build_system_prompt(data),
                    provider=data["model_config"]["provider"],
                    model=data["model_config"]["model"],
                    temperature=data["model_config"]["temperature"],
                    voice_id=data["voice"]["id"],
                    voice_stability=data["voice"]["stability"],
                    voice_clarity=data["voice"]["clarity"],
                )
                configs.append(config)
                logger.info(f"Loaded character configuration: {config.name}")

    except Exception as e:
        logger.error(f"Error loading character configurations: {e}")

    return configs


def _build_system_prompt(character_data: Dict) -> str:
    """Build a comprehensive system prompt from character data."""
    prompt_parts = [
        "CORE RESPONSE RULES:",
        "- You MUST respond with EXACTLY ONE sentence or question.",
        "- Your response MUST NOT be longer than 30 words.",
        "- Your response MUST use basic punctuation (period or question mark).",
        "- Your response MUST NOT contain multiple sentences or compound sentences.",
        "- Your response MUST NOT use semicolons or conjunctions to combine thoughts.",
        "\nCHARACTER DEFINITION:",
        f"You are {character_data['name']}, {character_data['description']}.",
        character_data["character_definition"]["background"],
        "\nCore Traits:",
        "- " + "\n- ".join(character_data["character_definition"]["core_traits"]),
        "\nSpeech Style:",
        "- Vocabulary: "
        + character_data["character_definition"]["speech_style"]["vocabulary_level"],
        "- Tone: " + character_data["character_definition"]["speech_style"]["tone"],
        "- Patterns:\n  - "
        + "\n  - ".join(
            character_data["character_definition"]["speech_style"]["patterns"]
        ),
        "\nInteraction Guidelines:",
        f"Primary Goal: {character_data['interaction_guidelines']['primary_goal']}",
        f"Strategy: {character_data['interaction_guidelines']['conversation_strategy']}",
        "\nMust Rules:",
        "- " + "\n- ".join(character_data["interaction_guidelines"]["must_rules"]),
        "\nMust Not Rules:",
        "- " + "\n- ".join(character_data["interaction_guidelines"]["must_not_rules"]),
        "\nFINAL REMINDER: Respond with exactly one sentence or question, no more than 30 words.",
    ]

    return "\n".join(prompt_parts)
