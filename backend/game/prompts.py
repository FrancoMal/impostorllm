"""
LLM prompt templates for the Impostor Word Game
Separate prompts for INNOCENTS (know the word) and IMPOSTOR (doesn't know).
"""

import re

# =============================================================================
# WORD ROUND PROMPTS
# =============================================================================

WORD_ROUND_PROMPT_INNOCENT = """JUEGO: Palabra Impostor - Ronda {ronda}
Eres: {modelo}
Tu turno: #{tu_turno}

=== LA PALABRA SECRETA ===
"{palabra}"
(Solo tu y otros inocentes la conocen. El impostor NO la sabe.)

=== TU MISION ===
Di UNA palabra que se RELACIONE con "{palabra}" de forma SUTIL:
- NO seas obvio (eso ayuda al impostor a adivinar)
- Piensa en: lugares, emociones, situaciones, objetos asociados, algo que puedas defender mas adelante
- Debe tener justificacion logica si te cuestionan en el debate

Palabras dichas hasta ahora:
{palabras_anteriores}

=== PROHIBIDO ===
- Decir "{palabra}" directamente
- Sinonimos muy obvios o la categoria directa
- Repetir alguna de {palabras_anteriores} o muy similares
- tampoco puedes decir la {palabra}
Responde con UNA sola palabra en espanol:"""

WORD_ROUND_PROMPT_IMPOSTOR = """JUEGO: Palabra Impostor - Ronda {ronda}
Eres: {modelo}
Tu turno: #{tu_turno}

=== ERES EL IMPOSTOR ===
NO conoces la palabra secreta. Los demas SI la conocen.

Palabras dichas hasta ahora:
{palabras_anteriores}

=== TU MISION ===
OBSERVA: Que patron o tema conecta las palabras anteriores?
INVENTA: Una palabra que encaje naturalmente con ese patron
PREPARA: Una justificacion por si te cuestionan en el debate

=== IMPORTANTE ===
- Tu palabra sera analizada - debe ser DEFENDIBLE
- Recuerda tu TEORIA sobre la palabra secreta
- La necesitaras en el debate y rondas futuras
- Debes decir si o si una palabra, no puedes dejarla vacia. Del caso contrario pierdes automaticamente y serás eliminado.
Responde con UNA sola palabra en espanol:"""

# =============================================================================
# DEBATE PROMPTS
# =============================================================================

DEBATE_PROMPT_INNOCENT = """JUEGO: Palabra Impostor - Debate
Eres: {modelo}

=== TU SITUACION ===
Conoces la palabra secreta: {palabra_secreta} y no puedes decirla en el debate.
(Esta PROHIBIDO decirla o usar sinonimos directos)
Tu dijiste: "{tu_palabra}"

=== JUGADORES EN JUEGO ===
Activos: {jugadores_activos}
{jugadores_eliminados}

=== PALABRAS DICHAS ===
{todas_las_palabras}

=== DEBATE PREVIO ===
{historial_debate}

=== TU MISION ===
- El debate es para acusar a alguien, no es necesario que todas las palabras tengan relacion en sí, solo relacion en torno a la {palabra_secreta}
- Defender y/o cuestionar a alguien (puedes cambiar de opinion)
- La idea es que tengas a alguien en la mira por la palabra que dijo anteriormente. La que menos relacione con el tema es la que se acusa y la justificación con la que se definede no te calza.

=== COMO JUGAR EL DEBATE ===
DEFENDER tu palabra:
- Decir muy brevemente porque no eres sin decir la palabra secreta para justificarte sino referirte ligeramente al topico
- NO uses la palabra secreta para justificarte (esta prohibido decirla) y además ayudas al impostor a que sepa cual es la palabra, por eso debes aliarte con el resto de inocentes.
- Para justificarte no puedes decir la palabra secreta, es razon de expulsión a ti mismo.
- tambien puede defender a alguien si le parece buena la palabra que dijo, esto ayuda a ganar confianza tambien.
INVESTIGAR al impostor:
- Duda de las palabras que no tinen sentido para nada
- si está vacío es bastante sospechoso.
- No olvides, lo mas imporante es {todas_las_palabras} que dijeron para deducir quien es el impostor.
- Quien dio una palabra DESCONECTADA del tema?
- Deduce quien puede ser a través de descarte de posibles candidatos
- Si alguien no dijo palabra es muy posiblemente el impostor.
Responde en 2-3 oraciones sin decir la {palabra_secreta} y debes ser consciente de {tu_palabra} (defiendete y/o cuestiona a alguien):"""

DEBATE_PROMPT_IMPOSTOR = """JUEGO: Palabra Impostor - Debate
Eres: {modelo}

=== ERES EL IMPOSTOR ===
NO conoces la palabra secreta.
Tu dijiste: "{tu_palabra}"

=== JUGADORES EN JUEGO ===
Activos: {jugadores_activos}
{jugadores_eliminados}

=== PALABRAS DICHAS ===
{todas_las_palabras}

=== DEBATE PREVIO ===
{historial_debate}

=== TU ESTRATEGIA ===
DEFENDER tu palabra:
- Conecta "{tu_palabra}" con las palabras de OTROS jugadores
- Actua con CONFIANZA, como si conocieras la palabra

DESVIAR SOSPECHAS:
- Cuestiona a otros para parecer un inocente investigando
- Si te acusan, contraargumenta con logica o intenta relacionar la palabra con la palabra que crees que sea teniendo en cuenta lo que dice el resto

APRENDER:
- Presta atencion a como se defienden los inocentes
- Deduce cual podria ser la palabra secreta
- Esta teoria te servira si sobrevives o te eliminan

Responde en 2-3 oraciones sin decir {palabra_secreta} (defiendete O cuestiona a alguien):"""

# =============================================================================
# VOTING PROMPT
# =============================================================================

VOTING_PROMPT = """VOTACION FINAL - Eres {modelo}

=== TU PARTICIPACION ===
Tu dijiste la palabra: "{tu_palabra}"

=== JUGADORES EN JUEGO ===
Activos (puedes votar por ellos): {jugadores_activos}
{jugadores_eliminados}

=== TODAS LAS PALABRAS DICHAS (por ronda) ===
{palabras_jugadores}

=== CONVERSACION COMPLETA DEL DEBATE ===
{debate_completo}

=== ANALIZA ANTES DE VOTAR ===
Considera TODO lo que paso en la partida:
1. COHERENCIA: Quien dio palabras que NO encajan con el tema comun?
2. ORDEN: Quien hablo DESPUES y parece haber COPIADO patrones de otros?
3. DEFENSAS: Quien tuvo justificaciones DEBILES o EVASIVAS en el debate?
4. COMPORTAMIENTO: Quien EVADIO preguntas o cambio de tema sospechosamente?
5. CONTRADICCIONES: Quien dijo cosas inconsistentes durante el debate?

=== TU VOTO ===
Jugadores validos (no puedes votarte): {nombres_validos}

RESPONDE CON ESTE FORMATO EXACTO:
VOTO: [nombre del jugador]
RAZON: [1-2 oraciones explicando tu razonamiento]"""

# =============================================================================
# IMPOSTOR GUESS PROMPT
# =============================================================================

IMPOSTOR_GUESS_PROMPT = """ULTIMA OPORTUNIDAD - Eres {modelo}

Fuiste descubierto como IMPOSTOR.
Pero puedes GANAR si adivinas la palabra secreta.

=== PALABRAS QUE DIJERON LOS INOCENTES ===
{todas_las_palabras}

=== LO QUE SE DIJO EN EL DEBATE ===
{historial_debate}

=== ANALIZA ===
- Que TEMA comun conecta todas esas palabras?
- Que palabra estaban describiendo SIN decirla?
- Piensa: si hubieras conocido la palabra, cual seria?

RESPONDE CON UNA SOLA PALABRA (tu mejor teoria):"""

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clean_llm_response(response: str) -> str:
    """Clean LLM response by removing thinking tags and artifacts."""
    if not response:
        return ""

    # Remove <think>...</think> blocks (deepseek-r1, qwen3 style) - with or without closing tag
    # Handle multiple variations: <think>, < think>, <thinking>, etc.
    response = re.sub(r'<\s*think\s*>.*?<\s*/\s*think\s*>', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<\s*thinking\s*>.*?<\s*/\s*thinking\s*>', '', response, flags=re.DOTALL | re.IGNORECASE)

    # Remove unclosed <think> tags (everything from <think> to end)
    response = re.sub(r'<\s*think\s*>.*', '', response, flags=re.DOTALL | re.IGNORECASE)
    response = re.sub(r'<\s*thinking\s*>.*', '', response, flags=re.DOTALL | re.IGNORECASE)

    # Remove orphan closing tags
    response = re.sub(r'<\s*/\s*think\s*>', '', response, flags=re.IGNORECASE)
    response = re.sub(r'<\s*/\s*thinking\s*>', '', response, flags=re.IGNORECASE)

    # Remove other common artifacts and HTML-like tags
    response = re.sub(r'<[^>]+>', '', response)  # Remove any remaining HTML-like tags
    response = re.sub(r'\[.*?\]', '', response)  # Remove [brackets]
    response = re.sub(r'\(pensando.*?\)', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\(thinking.*?\)', '', response, flags=re.IGNORECASE)
    response = re.sub(r'^\s*(respuesta|answer|output|response):\s*', '', response, flags=re.IGNORECASE | re.MULTILINE)

    # Remove lines that start with thinking indicators
    lines = response.split('\n')
    cleaned_lines = []
    for line in lines:
        line_lower = line.strip().lower()
        if not line_lower.startswith(('pensando:', 'thinking:', 'razonamiento:', 'analisis:', '<think', '</think')):
            cleaned_lines.append(line)
    response = '\n'.join(cleaned_lines)

    # Clean whitespace
    response = response.strip()

    # Remove quotes if the entire response is quoted
    if (response.startswith('"') and response.endswith('"')) or \
       (response.startswith("'") and response.endswith("'")):
        response = response[1:-1]

    return response.strip()


def censor_secret_word(response: str, secret_word: str) -> str:
    """Censor the secret word if it appears in the response."""
    if not response or not secret_word:
        return response

    # Case-insensitive replacement
    pattern = re.compile(re.escape(secret_word), re.IGNORECASE)
    censored = pattern.sub('****', response)
    return censored


# Words that should never be used as player responses (LLM artifacts)
FORBIDDEN_WORDS = {'think', 'thinking', 'pensando', 'respuesta', 'answer', 'output', 'response'}


def is_valid_word(word: str) -> bool:
    """Check if a word is valid (not an LLM artifact)."""
    return word.lower() not in FORBIDDEN_WORDS and len(word) > 1


# =============================================================================
# FORMAT FUNCTIONS
# =============================================================================

def format_word_round_prompt(
    model_name: str,
    word: str,
    previous_words: list[tuple[str, str]],
    current_turn: int = 1,
    current_round: int = 1,
    is_impostor: bool = False
) -> str:
    """Format the word round prompt - different for innocent vs impostor."""
    if previous_words:
        words_str = "\n".join([f"  #{i+1} {name}: {w}" for i, (name, w) in enumerate(previous_words)])
    else:
        words_str = "  (Eres el primero en hablar - no hay pistas aun)"

    if is_impostor:
        return WORD_ROUND_PROMPT_IMPOSTOR.format(
            modelo=model_name,
            palabras_anteriores=words_str,
            tu_turno=current_turn,
            ronda=current_round
        )
    else:
        return WORD_ROUND_PROMPT_INNOCENT.format(
            modelo=model_name,
            palabra=word,
            palabras_anteriores=words_str,
            tu_turno=current_turn,
            ronda=current_round
        )


def format_debate_prompt(
    model_name: str,
    word: str,
    all_words: list[tuple[str, str]],
    debate_history: list[tuple[str, str]],
    player_said_word: str = "",
    active_players: list[str] = None,
    eliminated_players: list[str] = None
) -> str:
    """Format the debate prompt - different for impostor vs innocent."""
    # Include turn number to show who spoke first vs who could have copied
    words_str = "\n".join([f"  #{i+1} {name}: {w}" for i, (name, w) in enumerate(all_words)])

    if debate_history:
        history_str = "\n".join([f"  {name}: \"{msg}\"" for name, msg in debate_history[-6:]])
    else:
        history_str = "  (El debate acaba de comenzar)"

    # Format active and eliminated players
    activos_str = ", ".join(active_players) if active_players else "todos"
    if eliminated_players:
        eliminados_str = f"Eliminados: {', '.join(eliminated_players)} (ya no participan)"
    else:
        eliminados_str = ""

    # Use different template based on role - impostor gets "IMPOSTOR" as word
    is_impostor = word.upper() == "IMPOSTOR"
    template = DEBATE_PROMPT_IMPOSTOR if is_impostor else DEBATE_PROMPT_INNOCENT

    if is_impostor:
        return template.format(
            modelo=model_name,
            tu_palabra=player_said_word,
            jugadores_activos=activos_str,
            jugadores_eliminados=eliminados_str,
            todas_las_palabras=words_str,
            historial_debate=history_str
        )
    else:
        # Innocent players get the secret word (censored in prompt display)
        return template.format(
            modelo=model_name,
            palabra_secreta=word,  # The actual secret word for context
            tu_palabra=player_said_word,
            jugadores_activos=activos_str,
            jugadores_eliminados=eliminados_str,
            todas_las_palabras=words_str,
            historial_debate=history_str
        )


def format_voting_prompt(
    model_name: str,
    player_words: list[tuple[str, str]],
    debate_history: list[tuple[str, str]] = None,
    player_said_word: str = "",
    active_players: list[str] = None,
    eliminated_players: list[str] = None
) -> str:
    """Format the voting prompt with FULL debate context and justification request."""
    words_str = "\n".join([f"  #{i+1} {name}: {w}" for i, (name, w) in enumerate(player_words)])

    # Include FULL debate history, not just last 8 messages
    if debate_history:
        debate_str = "\n".join([f"  {name}: \"{msg}\"" for name, msg in debate_history])
    else:
        debate_str = "  (No hubo debate)"

    # Get valid player names from player_words (excludes self since voter is not in player_words)
    valid_names = [name for name, _ in player_words]
    names_str = ", ".join(valid_names[:-1]) + " o " + valid_names[-1] if len(valid_names) > 1 else valid_names[0] if valid_names else ""

    # Format active and eliminated players
    activos_str = ", ".join(active_players) if active_players else names_str
    if eliminated_players:
        eliminados_str = f"Eliminados: {', '.join(eliminated_players)} (NO puedes votar por ellos)"
    else:
        eliminados_str = ""

    return VOTING_PROMPT.format(
        modelo=model_name,
        tu_palabra=player_said_word,
        jugadores_activos=activos_str,
        jugadores_eliminados=eliminados_str,
        palabras_jugadores=words_str,
        debate_completo=debate_str,
        nombres_validos=names_str
    )


def parse_vote_response(response: str, valid_names: list[str]) -> tuple[str, str]:
    """Parse vote response to extract player name and justification.

    Returns: (voted_for_name, justification)
    """
    response = clean_llm_response(response)

    voted_for = ""
    justification = ""

    # Try to parse structured format: VOTO: X / RAZON: Y
    lines = response.strip().split('\n')

    for line in lines:
        line_lower = line.lower().strip()

        # Extract vote
        if line_lower.startswith('voto:'):
            vote_part = line[5:].strip()  # After "VOTO:"
            for name in valid_names:
                if name.lower() in vote_part.lower():
                    voted_for = name
                    break

        # Extract justification
        elif line_lower.startswith('razon:') or line_lower.startswith('razón:'):
            justification = line.split(':', 1)[1].strip() if ':' in line else ""

    # Fallback: if no structured format, try to find name anywhere
    if not voted_for:
        response_lower = response.lower()
        for name in valid_names:
            if name.lower() in response_lower:
                voted_for = name
                break

    # If still no vote but we have response, use first word matching any name prefix
    if not voted_for:
        words = response.lower().split()
        for word in words:
            for name in valid_names:
                if name.lower().startswith(word) or word.startswith(name.lower()):
                    voted_for = name
                    break
            if voted_for:
                break

    # If no structured justification, use everything after the vote as justification
    if not justification and voted_for:
        # Try to extract reasoning from unstructured response
        response_after_vote = response.lower().split(voted_for.lower(), 1)
        if len(response_after_vote) > 1:
            justification = response_after_vote[1].strip()
            # Clean up common prefixes
            for prefix in ['porque', 'ya que', 'dado que', 'pues', '.', ',', ':']:
                if justification.lower().startswith(prefix):
                    justification = justification[len(prefix):].strip()

    return voted_for, justification


def format_impostor_guess_prompt(
    model_name: str,
    all_words: list[tuple[str, str]],
    debate_history: list[tuple[str, str]] = None
) -> str:
    """Format the impostor guess prompt."""
    words_str = "\n".join([f"  - {name}: {w}" for name, w in all_words])

    if debate_history:
        history_str = "\n".join([f"  {name}: \"{msg}\"" for name, msg in debate_history[-10:]])
    else:
        history_str = "  (No hubo debate)"

    return IMPOSTOR_GUESS_PROMPT.format(
        modelo=model_name,
        todas_las_palabras=words_str,
        historial_debate=history_str
    )
