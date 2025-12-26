"""
LLM Chat-Based Context Management for the Impostor Word Game
Version 2: Persistent conversation per player using Ollama's chat format.

This system maintains full context throughout the game by using
a chat-based approach where each player has their own conversation history.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional
from .prompts import clean_llm_response, censor_secret_word, parse_vote_response, is_valid_word


# =============================================================================
# CONSTANTS - GAME RULES
# =============================================================================

GAME_RULES = """REGLAS DEL JUEGO "PALABRA IMPOSTOR":
1. Todos los jugadores menos uno (el impostor) conocen la palabra secreta
2. El impostor NO sabe cual es la palabra secreta
3. En cada ronda, cada jugador dice UNA palabra relacionada con la secreta
4. Luego hay un debate donde se discute quien es el impostor
5. Se vota para eliminar al sospechoso
6. Si eliminan al impostor, este tiene UNA oportunidad de adivinar la palabra
7. Ganan los inocentes si el impostor no adivina, gana el impostor si adivina o no es descubierto"""


# =============================================================================
# SYSTEM PROMPTS (Se envian una vez al inicio del juego)
# =============================================================================

SYSTEM_PROMPT_INNOCENT = """Eres {player_name}, un jugador en "Palabra Impostor".

{game_rules}

=== TU ROL ===
Eres INOCENTE. Conoces la palabra secreta: "{secret_word}"

=== TUS OBJETIVOS ===
1. Decir palabras que se RELACIONEN con "{secret_word}" de forma SUTIL
2. NO ser tan obvio (eso ayuda al impostor a adivinar)
3. Identificar al impostor analizando las palabras de los demas
4. Defender tu palabra si te acusan
5. NUNCA decir la palabra secreta directamente

=== ESTRATEGIA PARA PALABRAS ===
- Piensa en: lugares, emociones, situaciones, objetos asociados
- Debe tener justificacion logica si te cuestionan en el debate
- NO uses sinonimos muy obvios o la categoria directa

=== ESTRATEGIA PARA EL DEBATE ===
- El debate es para acusar a alguien basandote en sus palabras
- La que menos relacione con el tema es sospechosa
- NO uses la palabra secreta para justificarte (esta prohibido)
- Puedes defender a alguien si te parece buena su palabra

=== IMPORTANTE ===
- Esta PROHIBIDO decir "{secret_word}" o sinonimos muy obvios
- Si dices la palabra secreta, seras eliminado automaticamente
- Debes colaborar con otros inocentes para encontrar al impostor
- Responde siempre en espanol"""

SYSTEM_PROMPT_IMPOSTOR = """Eres {player_name}, un jugador en "Palabra Impostor".

{game_rules}

=== TU ROL ===
Eres el IMPOSTOR. NO conoces la palabra secreta.

=== TUS OBJETIVOS ===
1. OBSERVAR las palabras de los demas para deducir el tema
2. Decir palabras que ENCAJEN con el patron que observas
3. FINGIR que conoces la palabra secreta
4. DESVIAR sospechas hacia otros jugadores
5. Si te descubren, intenta ADIVINAR la palabra secreta

=== ESTRATEGIA PARA PALABRAS ===
- OBSERVA: Que patron o tema conecta las palabras anteriores?
- INVENTA: Una palabra que encaje naturalmente con ese patron
- PREPARA: Una justificacion por si te cuestionan en el debate
- Tu palabra sera analizada - debe ser DEFENDIBLE
- Recuerda tu TEORIA sobre la palabra secreta para rondas futuras

=== ESTRATEGIA PARA EL DEBATE ===
- Conecta tu palabra con las palabras de OTROS jugadores
- Actua con CONFIANZA, como si conocieras la palabra
- Cuestiona a otros para parecer un inocente investigando
- Si te acusan, contraargumenta con logica
- Presta atencion a como se defienden los inocentes para aprender

=== IMPORTANTE ===
- Debes decir si o si una palabra, no puedes dejarla vacia
- Del caso contrario pierdes automaticamente y seras eliminado
- Responde siempre en espanol"""


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ChatMessage:
    """A single message in the conversation."""
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class PlayerConversation:
    """
    Manages the conversation history for a single player.
    This maintains full context throughout the game.
    """
    player_id: str
    player_name: str
    model: str
    is_impostor: bool
    secret_word: Optional[str]  # None for impostor
    messages: list[ChatMessage] = field(default_factory=list)
    player_word: Optional[str] = None  # Word they said in word round
    words_said: list[str] = field(default_factory=list)  # All words said across rounds
    is_eliminated: bool = False

    def __post_init__(self):
        """Initialize with system prompt based on role."""
        self._init_system_prompt()

    def _init_system_prompt(self):
        """Set up the initial system message with player's role."""
        if self.is_impostor:
            system_content = SYSTEM_PROMPT_IMPOSTOR.format(
                player_name=self.player_name,
                game_rules=GAME_RULES
            )
        else:
            system_content = SYSTEM_PROMPT_INNOCENT.format(
                player_name=self.player_name,
                game_rules=GAME_RULES,
                secret_word=self.secret_word
            )

        self.messages.append(ChatMessage(role="system", content=system_content))

    def add_user_message(self, content: str):
        """Add a user message (game events, other players' actions)."""
        self.messages.append(ChatMessage(role="user", content=content))

    def add_assistant_message(self, content: str):
        """Add an assistant message (this player's response)."""
        self.messages.append(ChatMessage(role="assistant", content=content))

    def get_messages_for_ollama(self) -> list[dict]:
        """Get messages in Ollama's expected format."""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message content."""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None

    def get_context_summary(self) -> str:
        """Get a summary of the conversation for debugging."""
        return f"Player {self.player_name}: {len(self.messages)} messages, word: {self.player_word}"


# =============================================================================
# GAME CONVERSATION MANAGER
# =============================================================================

class GameConversationManager:
    """
    Manages all player conversations for a single game.
    Handles broadcasting game events to all players.
    """

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.conversations: dict[str, PlayerConversation] = {}
        self.current_round: int = 1
        self.debate_round: int = 1

    def init_player(
        self,
        player_id: str,
        player_name: str,
        model: str,
        is_impostor: bool,
        secret_word: Optional[str] = None
    ) -> PlayerConversation:
        """Initialize a player's conversation."""
        conv = PlayerConversation(
            player_id=player_id,
            player_name=player_name,
            model=model,
            is_impostor=is_impostor,
            secret_word=secret_word
        )
        self.conversations[player_id] = conv
        return conv

    def get_conversation(self, player_id: str) -> Optional[PlayerConversation]:
        """Get a player's conversation."""
        return self.conversations.get(player_id)

    def get_all_active_conversations(self) -> list[PlayerConversation]:
        """Get all non-eliminated players' conversations."""
        return [c for c in self.conversations.values() if not c.is_eliminated]

    def broadcast_to_all(self, content: str, exclude_player_id: Optional[str] = None):
        """Add a user message to all players' conversations."""
        for player_id, conv in self.conversations.items():
            if player_id != exclude_player_id and not conv.is_eliminated:
                conv.add_user_message(content)

    def broadcast_word(self, speaker_id: str, speaker_name: str, word: str):
        """Broadcast when a player says their word."""
        message = format_word_announcement(speaker_name, word)
        self.broadcast_to_all(message, exclude_player_id=speaker_id)

    def broadcast_debate_message(self, speaker_id: str, speaker_name: str, message: str):
        """Broadcast a debate message to all other players."""
        formatted = format_debate_announcement(speaker_name, message)
        self.broadcast_to_all(formatted, exclude_player_id=speaker_id)

    def broadcast_vote(self, voter_name: str, voted_for: str, reason: str):
        """Broadcast a vote to all players."""
        message = format_vote_announcement(voter_name, voted_for, reason)
        self.broadcast_to_all(message)

    def broadcast_elimination(self, player_name: str, was_impostor: bool):
        """Broadcast when a player is eliminated."""
        message = format_elimination_announcement(player_name, was_impostor)
        self.broadcast_to_all(message)

    def get_all_words(self) -> list[tuple[str, str]]:
        """Get all words said by all players."""
        words = []
        for conv in self.conversations.values():
            if conv.player_word:
                words.append((conv.player_name, conv.player_word))
        return words

    def get_active_player_names(self) -> list[str]:
        """Get names of all non-eliminated players."""
        return [c.player_name for c in self.conversations.values() if not c.is_eliminated]

    def get_eliminated_player_names(self) -> list[str]:
        """Get names of all eliminated players."""
        return [c.player_name for c in self.conversations.values() if c.is_eliminated]


# =============================================================================
# FORMAT FUNCTIONS - REQUESTS (what we ask the player)
# =============================================================================

def format_word_round_request(
    round_number: int,
    turn_number: int,
    previous_words: list[tuple[str, str]]
) -> str:
    """Format the request for a player to say their word."""

    if previous_words:
        words_str = "\n".join([f"  #{i+1} {name}: {word}" for i, (name, word) in enumerate(previous_words)])
        words_section = f"Palabras dichas hasta ahora:\n{words_str}"
    else:
        words_section = "(Eres el primero en hablar - no hay pistas aun)"

    return f"""=== RONDA DE PALABRAS #{round_number} ===
Tu turno: #{turn_number}

{words_section}

=== RECUERDA ===
- Di UNA palabra que se RELACIONE con la palabra secreta de forma SUTIL
- NO seas obvio (eso ayuda al impostor a adivinar)
- Piensa en: lugares, emociones, situaciones, objetos asociados
- Debe tener justificacion logica si te cuestionan en el debate
- NO repitas palabras ya dichas ni muy similares

Responde con UNA SOLA PALABRA en espanol:"""


def format_debate_turn_request(
    active_players: list[str],
    eliminated_players: list[str] = None,
    player_word: str = "",
    all_words: list[tuple[str, str]] = None
) -> str:
    """Format the request for a player to speak in the debate."""

    activos = ", ".join(active_players)
    eliminados = f"\nEliminados: {', '.join(eliminated_players)} (ya no participan)" if eliminated_players else ""

    # Include all words for reference
    if all_words:
        words_str = "\n".join([f"  #{i+1} {name}: {word}" for i, (name, word) in enumerate(all_words)])
        words_section = f"\n=== PALABRAS DICHAS ===\n{words_str}\n"
    else:
        words_section = ""

    tu_palabra = f"\nTu dijiste: \"{player_word}\"" if player_word else ""

    return f"""=== TU TURNO EN EL DEBATE ===
Jugadores activos: {activos}{eliminados}{tu_palabra}
{words_section}
=== COMO JUGAR EL DEBATE ===
DEFENDER tu palabra:
- Explica brevemente por que tu palabra tiene sentido
- NO uses la palabra secreta para justificarte (esta prohibido)
- Puedes defender a alguien si te parece buena su palabra

INVESTIGAR al impostor:
- Duda de las palabras que no tienen sentido con el tema
- Quien dio una palabra DESCONECTADA del tema?
- Si alguien no dijo palabra es muy posiblemente el impostor
- Deduce quien puede ser a traves de descarte

Responde en 2-3 oraciones (defiendete Y/O cuestiona a alguien):"""


def format_vote_request(
    votable_players: list[str],
    all_words: list[tuple[str, str]],
    eliminated_players: list[str] = None,
    player_word: str = ""
) -> str:
    """Format the request for a player to vote."""

    words_str = "\n".join([f"  #{i+1} {name}: {word}" for i, (name, word) in enumerate(all_words)])
    votables = ", ".join(votable_players[:-1]) + " o " + votable_players[-1] if len(votable_players) > 1 else votable_players[0] if votable_players else ""
    eliminados = f"\nEliminados (NO puedes votar por ellos): {', '.join(eliminated_players)}" if eliminated_players else ""
    tu_palabra = f"\nTu dijiste: \"{player_word}\"" if player_word else ""

    return f"""=== VOTACION FINAL ==={tu_palabra}

=== TODAS LAS PALABRAS DICHAS ===
{words_str}
{eliminados}

=== ANALIZA ANTES DE VOTAR ===
Considera TODO lo que paso en la partida:
1. COHERENCIA: Quien dio palabras que NO encajan con el tema comun?
2. ORDEN: Quien hablo DESPUES y parece haber COPIADO patrones de otros?
3. DEFENSAS: Quien tuvo justificaciones DEBILES o EVASIVAS en el debate?
4. COMPORTAMIENTO: Quien EVADIO preguntas o cambio de tema sospechosamente?
5. CONTRADICCIONES: Quien dijo cosas inconsistentes durante el debate?

=== TU VOTO ===
Jugadores validos (no puedes votarte a ti mismo): {votables}

RESPONDE CON ESTE FORMATO EXACTO:
VOTO: [nombre del jugador]
RAZON: [1-2 oraciones explicando tu razonamiento]"""


def format_impostor_guess_request(
    all_words: list[tuple[str, str]],
    debate_history: list[tuple[str, str]] = None
) -> str:
    """Format the request for the eliminated impostor to guess the word."""

    words_str = "\n".join([f"  - {name}: {word}" for name, word in all_words])

    if debate_history:
        history_str = "\n".join([f"  {name}: \"{msg}\"" for name, msg in debate_history[-10:]])
        debate_section = f"\n=== LO QUE SE DIJO EN EL DEBATE ===\n{history_str}\n"
    else:
        debate_section = ""

    return f"""=== ULTIMA OPORTUNIDAD ===

Fuiste descubierto como IMPOSTOR.
Pero puedes GANAR si adivinas la palabra secreta.

=== PALABRAS QUE DIJERON LOS INOCENTES ===
{words_str}
{debate_section}
=== ANALIZA ===
- Que TEMA comun conecta todas esas palabras?
- Que palabra estaban describiendo SIN decirla?
- Piensa: si hubieras conocido la palabra, cual seria?

RESPONDE CON UNA SOLA PALABRA (tu mejor teoria):"""


# =============================================================================
# FORMAT FUNCTIONS - ANNOUNCEMENTS (what happened in the game)
# =============================================================================

def format_word_announcement(player_name: str, word: str) -> str:
    """Format announcement when a player says their word."""
    return f"[PALABRA] {player_name} dice: \"{word}\""


def format_debate_announcement(player_name: str, message: str) -> str:
    """Format announcement when a player speaks in debate."""
    return f"[DEBATE] {player_name}: \"{message}\""


def format_vote_announcement(voter_name: str, voted_for: str, reason: str) -> str:
    """Format announcement when a player votes."""
    return f"[VOTO] {voter_name} vota por {voted_for}: \"{reason}\""


def format_elimination_announcement(player_name: str, was_impostor: bool) -> str:
    """Format announcement when a player is eliminated."""
    role = "el IMPOSTOR" if was_impostor else "INOCENTE"
    emoji = "🎭" if was_impostor else "😇"
    return f"[ELIMINADO] {emoji} {player_name} fue eliminado. Era {role}."


def format_round_start(round_number: int) -> str:
    """Format announcement for start of a new word round."""
    return f"=== COMIENZA RONDA {round_number} DE PALABRAS ==="


def format_debate_start() -> str:
    """Format announcement for start of debate."""
    return "=== COMIENZA EL DEBATE ==="


def format_voting_start() -> str:
    """Format announcement for start of voting."""
    return "=== COMIENZA LA VOTACION ==="


def format_game_result(winner: str, secret_word: str, impostor_name: str) -> str:
    """Format the game result announcement."""
    if winner == "innocents":
        return f"""=== FIN DEL JUEGO ===
🎉 GANAN LOS INOCENTES
La palabra secreta era: "{secret_word}"
El impostor era: {impostor_name}"""
    else:
        return f"""=== FIN DEL JUEGO ===
🎭 GANA EL IMPOSTOR
La palabra secreta era: "{secret_word}"
El impostor {impostor_name} logro su objetivo."""


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def extract_single_word(response: str) -> str:
    """Extract a single word from a response."""
    cleaned = clean_llm_response(response)

    # Take first word only
    words = cleaned.split()
    if words:
        # Remove punctuation
        word = words[0].strip('.,!?:;"\'()[]{}')
        return word

    return cleaned


def process_word_response(response: str, secret_word: str = None) -> str:
    """Process and validate a word round response."""
    word = extract_single_word(response)

    # Check if valid
    if not is_valid_word(word):
        return ""

    # Censor if matches secret word
    if secret_word:
        word = censor_secret_word(word, secret_word)

    return word


def process_debate_response(response: str, secret_word: str = None) -> str:
    """Process a debate response."""
    cleaned = clean_llm_response(response)

    # Censor secret word if present
    if secret_word:
        cleaned = censor_secret_word(cleaned, secret_word)

    return cleaned


def process_vote_response(response: str, valid_names: list[str]) -> tuple[str, str]:
    """Process a vote response. Returns (voted_for, reason)."""
    return parse_vote_response(response, valid_names)


def process_guess_response(response: str) -> str:
    """Process the impostor's guess response."""
    return extract_single_word(response)


# =============================================================================
# OLLAMA CHAT INTERFACE HELPER
# =============================================================================

# Thinking models that need /no_think flag
THINKING_MODELS = ['deepseek-r1', 'qwq']

# Set to True to print full conversation history for debugging
DEBUG_CONVERSATIONS = True


def _prepare_message_for_thinking_models(model: str, content: str) -> str:
    """Add /no_think flag for models that have extended thinking."""
    if any(tm in model.lower() for tm in THINKING_MODELS):
        return content + "\n/no_think"
    return content


async def get_player_response(
    conversation: PlayerConversation,
    ollama_client,  # OllamaClient instance
    request_message: str,
    max_tokens: int = 300
) -> str:
    """
    Get a response from a player using their conversation context.

    Args:
        conversation: The player's conversation history
        ollama_client: OllamaClient instance with .chat() method
        request_message: The message to add before getting response
        max_tokens: Maximum tokens in response

    Returns:
        The player's response text
    """
    # Prepare message for thinking models
    prepared_message = _prepare_message_for_thinking_models(
        conversation.model,
        request_message
    )

    # Add the request as a user message
    conversation.add_user_message(prepared_message)

    # Get response from Ollama
    messages = conversation.get_messages_for_ollama()

    # Debug: print conversation history
    if DEBUG_CONVERSATIONS:
        print(f"\n{'='*60}")
        print(f"[CHAT] {conversation.player_name} ({conversation.model}) - {len(messages)} mensajes")
        print(f"{'='*60}")
        for i, msg in enumerate(messages):
            role = msg['role'].upper()
            content = msg['content']
            # Truncate long messages for readability
            if len(content) > 300:
                content = content[:300] + f"... (+{len(msg['content'])-300} chars)"
            print(f"[{i+1}] {role}:\n{content}\n")
        print(f"{'='*60}\n")

    try:
        response = await ollama_client.chat(
            model=conversation.model,
            messages=messages,
            max_tokens=max_tokens
        )
    except Exception as e:
        print(f"[ERROR] Failed to get response from {conversation.model}: {e}")
        response = ""

    # Clean the response
    response = clean_llm_response(response)

    # Add response to conversation history
    conversation.add_assistant_message(response)

    return response


async def get_word_from_player(
    conversation: PlayerConversation,
    ollama_client,
    round_number: int,
    turn_number: int,
    previous_words: list[tuple[str, str]]
) -> str:
    """
    Get a word from a player during the word round.

    Returns:
        The word said by the player (cleaned and validated)
    """
    request = format_word_round_request(round_number, turn_number, previous_words)

    response = await get_player_response(
        conversation,
        ollama_client,
        request,
        max_tokens=50  # Short response expected
    )

    # Process and validate the word
    word = process_word_response(response, conversation.secret_word)

    if word:
        conversation.player_word = word
        conversation.words_said.append(word)

    return word


async def get_debate_message_from_player(
    conversation: PlayerConversation,
    ollama_client,
    active_players: list[str],
    eliminated_players: list[str] = None,
    all_words: list[tuple[str, str]] = None
) -> str:
    """
    Get a debate message from a player.

    Returns:
        The debate message (cleaned and censored)
    """
    request = format_debate_turn_request(
        active_players,
        eliminated_players,
        player_word=conversation.player_word or "",
        all_words=all_words
    )

    response = await get_player_response(
        conversation,
        ollama_client,
        request,
        max_tokens=500  # Allow more elaborate debate messages
    )

    # Censor secret word if present
    return process_debate_response(response, conversation.secret_word)


async def get_vote_from_player(
    conversation: PlayerConversation,
    ollama_client,
    votable_players: list[str],
    all_words: list[tuple[str, str]],
    eliminated_players: list[str] = None
) -> tuple[str, str]:
    """
    Get a vote from a player.

    Returns:
        Tuple of (voted_for_name, reason)
    """
    request = format_vote_request(
        votable_players,
        all_words,
        eliminated_players,
        player_word=conversation.player_word or ""
    )

    response = await get_player_response(
        conversation,
        ollama_client,
        request,
        max_tokens=500  # Allow more elaborate vote justification
    )

    return process_vote_response(response, votable_players)


async def get_impostor_guess(
    conversation: PlayerConversation,
    ollama_client,
    all_words: list[tuple[str, str]],
    debate_history: list[tuple[str, str]] = None
) -> str:
    """
    Get the impostor's guess for the secret word.

    Returns:
        The guessed word
    """
    request = format_impostor_guess_request(all_words, debate_history)

    response = await get_player_response(
        conversation,
        ollama_client,
        request,
        max_tokens=100  # Allow some reasoning before the word
    )

    return process_guess_response(response)
