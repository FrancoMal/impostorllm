# Impostor LLM - Session Context
**Fecha**: 2025-12-24
**Estado**: Single-Model Mode Implementado y Verificado

## Resumen del Trabajo Completado

### 1. Modo Single-Model Implementado
- 5 instancias del mismo modelo LLM juegan con nombres diferentes
- Nombres: Alfa, Beta, Gamma, Delta, Epsilon, Zeta (hasta 6 jugadores)
- Selector de modelo en UI (dropdown)
- Slider para cantidad de jugadores (3-6)

### 2. Archivos Modificados
```
backend/
├── models/schemas.py      # GameConfig con single_model y player_count
├── game/state.py          # create_game() soporta single-model
├── game/logic.py          # Fixes de encoding Unicode
├── llm/players.py         # SINGLE_MODEL_PLAYERS y get_single_model_configs()
└── main.py                # v1.1 - Single-model mode support

frontend/
└── src/components/GameSetup.jsx  # Toggle y controles single-model
```

### 3. Bug Crítico Corregido
**Problema**: Caracteres Unicode (→, ✓, 🎭) causaban excepciones 'charmap' codec en Windows
**Ubicación**: `backend/game/logic.py`
**Fix**: Reemplazar con ASCII equivalentes:
- `→` → `->`
- `✓` → `[OK]`
- `🎭IMPOSTOR` → `[IMPOSTOR]`
- `válido` → `valido`

### 4. Partida de Prueba Exitosa
- **Palabra secreta**: "hotel"
- **Impostor**: Epsilon (qwen3:8b)
- **Resultado**: Impostor ganó (sobrevivió 3 rondas)
- **Eliminados**: Gamma (R1), Delta (R2), Beta (R3)

### 5. Modelos Disponibles en Ollama
- olmo2:7b
- qwen3:8b (usado para pruebas)
- gemma3:12b
- bakllava:latest
- dolphin-mistral:7b

## Estado Actual del Proyecto

### Funcionalidades Completas
- [x] Juego completo 5 jugadores LLM
- [x] Modo multi-modelo (diferentes modelos)
- [x] Modo single-model (mismo modelo, diferentes nombres)
- [x] Rondas de palabras con parsing de respuestas
- [x] Fase de debate con mensajes
- [x] Votación y eliminación
- [x] Detección de fin de juego
- [x] Leaderboard básico
- [x] Vista de espectador

### Comandos para Ejecutar
```bash
# Backend
cd G:\impostorllm\backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd G:\impostorllm\frontend
npm run dev
```

### URLs
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Observaciones de Gameplay

1. **qwen3:8b** tiende a usar `<think>` tags vacíos antes de responder
2. El impostor a veces da palabras muy obvias (ej: dijo "epsilon" su propio nombre)
3. Los LLMs votan de forma predecible (tienden a votar igual)
4. El parsing de votos funciona correctamente con el fix de encoding

## Próximos Pasos Sugeridos
- [ ] Mejorar prompts para votación más estratégica
- [ ] Agregar modo humano jugador
- [ ] Persistir leaderboard en archivo/DB
- [ ] Agregar más palabras al diccionario
- [ ] Probar con otros modelos (gemma3, olmo2)
