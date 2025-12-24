"""
LLM player configurations for the Impostor Word Game
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMPlayerConfig:
    """Configuration for an LLM player."""
    model: str
    display_name: str
    color: str
    icon: str  # Emoji or icon identifier


# Available LLM players (pool to choose from)
LLM_PLAYERS = [
    LLMPlayerConfig(
        model="gemma3:4b",
        display_name="gemma3",
        color="#FF6B6B",
        icon="💎"
    ),
    LLMPlayerConfig(
        model="mistral:7b",
        display_name="mistral",
        color="#4ECDC4",
        icon="🌪️"
    ),
    LLMPlayerConfig(
        model="olmo2:7b",
        display_name="olmo2",
        color="#45B7D1",
        icon="🧠"
    ),
    LLMPlayerConfig(
        model="dolphin-mistral:7b",
        display_name="dolphin",
        color="#96CEB4",
        icon="🐬"
    ),
    LLMPlayerConfig(
        model="qwen3:8b",
        display_name="qwen3",
        color="#DDA0DD",
        icon="🐼"
    ),
    LLMPlayerConfig(
        model="llama3.2:3b-instruct-q4_0",
        display_name="llama3.2",
        color="#FFA500",
        icon="🦙"
    ),
]

# Default players for quick start (5 players)
DEFAULT_PLAYERS = ["gemma3", "mistral", "olmo2", "dolphin", "qwen3"]


def get_player_config(model: str) -> Optional[LLMPlayerConfig]:
    """Get player config by model name."""
    for player in LLM_PLAYERS:
        if player.model == model or player.display_name == model:
            return player
    return None


def get_all_player_configs() -> list[LLMPlayerConfig]:
    """Get all player configurations."""
    return LLM_PLAYERS.copy()


def get_player_icon(model: str) -> str:
    """Get the icon for a player by model name."""
    config = get_player_config(model)
    return config.icon if config else "🤖"


def get_player_color(model: str) -> str:
    """Get the color for a player by model name."""
    config = get_player_config(model)
    return config.color if config else "#808080"


# Human player config
HUMAN_PLAYER = LLMPlayerConfig(
    model="human",
    display_name="Tu",
    color="#FFD700",
    icon="👤"
)


# Single-model player templates (for when all players use the same model)
SINGLE_MODEL_PLAYERS = [
    {"name": "Alfa", "color": "#FF6B6B", "icon": "🅰️"},
    {"name": "Beta", "color": "#4ECDC4", "icon": "🅱️"},
    {"name": "Gamma", "color": "#45B7D1", "icon": "Ⓖ"},
    {"name": "Delta", "color": "#96CEB4", "icon": "🔺"},
    {"name": "Epsilon", "color": "#DDA0DD", "icon": "Ⓔ"},
    {"name": "Zeta", "color": "#FFA500", "icon": "Ⓩ"},
]


def get_single_model_configs(model: str, count: int = 5) -> list[LLMPlayerConfig]:
    """Generate player configs for single-model mode."""
    configs = []
    for i in range(min(count, len(SINGLE_MODEL_PLAYERS))):
        template = SINGLE_MODEL_PLAYERS[i]
        configs.append(LLMPlayerConfig(
            model=model,
            display_name=template["name"],
            color=template["color"],
            icon=template["icon"]
        ))
    return configs
