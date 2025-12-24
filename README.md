# 🎭 Impostor LLM

Un juego de deducción social donde modelos de lenguaje (LLMs) compiten para identificar al impostor. Inspirado en juegos como "Palabra Secreta" y "Spyfall".

## 🎮 Reglas del Juego

### Objetivo
- **Inocentes**: Identificar y eliminar al impostor mediante votación
- **Impostor**: Pasar desapercibido y, si es descubierto, adivinar la palabra secreta

### Preparación
1. Se seleccionan 3-5 jugadores (modelos de IA disponibles en Ollama)
2. Se elige una categoría de palabras
3. Todos los jugadores excepto uno (el impostor) reciben la **palabra secreta**
4. El impostor NO conoce la palabra, solo sabe que es el impostor

### Fases del Juego

#### 1. 🎯 Ronda de Palabras
- Cada jugador dice **UNA palabra** relacionada con la palabra secreta
- Los inocentes deben dar pistas sutiles (no muy obvias para no ayudar al impostor)
- El impostor debe deducir el tema y dar una palabra que encaje sin conocer la palabra secreta
- Se juegan múltiples rondas

#### 2. 💬 Debate
- Los jugadores discuten quién podría ser el impostor
- Pueden defender sus palabras o cuestionar las de otros
- Duración configurable (por defecto 60 segundos)

#### 3. 🗳️ Votación
- Cada jugador vota por quién cree que es el impostor
- Deben justificar su voto con un razonamiento
- El jugador con más votos es eliminado

#### 4. 🎲 Resultado
- **Si el eliminado ES el impostor**: El impostor tiene una última oportunidad de adivinar la palabra secreta
  - Si adivina → **Gana el Impostor**
  - Si no adivina → **Ganan los Inocentes**
- **Si el eliminado NO es el impostor**: **Gana el Impostor**

### Estrategias

**Para Inocentes:**
- Da palabras relacionadas pero no obvias
- Observa quién da palabras que no encajan con el tema
- Presta atención al orden: quien habla después puede estar copiando patrones

**Para el Impostor:**
- Analiza las palabras de los demás para deducir el tema
- Da palabras genéricas que puedan encajar con varios temas
- Actúa con confianza en el debate
- Recuerda tu teoría sobre la palabra secreta

---

## 🛠️ Instalación Local

### Requisitos Previos

- **Python 3.10+**
- **Node.js 18+**
- **Ollama** instalado y corriendo ([ollama.ai](https://ollama.ai))

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/impostorllm.git
cd impostorllm
```

### 2. Instalar Modelos de Ollama

Descarga los modelos que quieras usar como jugadores:

```bash
# Modelos recomendados (ligeros y rápidos)
ollama pull gemma3
ollama pull mistral
ollama pull llama3
ollama pull phi4
ollama pull qwen3

# Verificar modelos instalados
ollama list
```

### 3. Configurar el Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar el Frontend

```bash
cd frontend

# Instalar dependencias
npm install
```

### 5. Ejecutar la Aplicación

**Terminal 1 - Backend:**
```bash
cd backend
# Activar entorno virtual si no está activo
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Iniciar servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 6. Jugar

Abre tu navegador en: **http://localhost:5173**

---

## 📁 Estructura del Proyecto

```
impostorllm/
├── backend/
│   ├── main.py              # Servidor FastAPI + WebSocket
│   ├── requirements.txt     # Dependencias Python
│   ├── game/
│   │   ├── logic.py         # Lógica principal del juego
│   │   ├── state.py         # Gestión de estado
│   │   ├── prompts.py       # Prompts para los LLMs
│   │   └── players.py       # Gestión de jugadores IA
│   ├── models/
│   │   └── schemas.py       # Modelos Pydantic
│   └── data/
│       └── words.json       # Categorías y palabras
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Componente principal
│   │   ├── components/      # Componentes React
│   │   ├── context/         # Estado global (GameContext)
│   │   ├── hooks/           # Custom hooks (WebSocket)
│   │   └── styles/          # Estilos CSS
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

## ⚙️ Configuración

### Variables de Entorno (Backend)

Crear archivo `.env` en `/backend`:

```env
OLLAMA_HOST=http://localhost:11434
DEFAULT_DEBATE_DURATION=60
```

### Agregar Palabras Personalizadas

Edita `backend/data/words.json`:

```json
{
  "categorias": {
    "tu_categoria": ["palabra1", "palabra2", "palabra3"]
  }
}
```

---

## 🎨 Modos de Juego

| Modo | Descripción |
|------|-------------|
| **Solo IA** | Todos los jugadores son modelos de IA (modo espectador) |
| **Con Humano** | Tú juegas junto a las IAs |

---

## 🤖 Modelos Soportados

Cualquier modelo disponible en Ollama. Recomendados:

| Modelo | Tamaño | Velocidad | Calidad |
|--------|--------|-----------|---------|
| gemma3 | ~2GB | ⚡⚡⚡ | ⭐⭐⭐ |
| mistral | ~4GB | ⚡⚡ | ⭐⭐⭐⭐ |
| llama3 | ~4GB | ⚡⚡ | ⭐⭐⭐⭐ |
| phi4 | ~2GB | ⚡⚡⚡ | ⭐⭐⭐ |
| qwen3 | ~2GB | ⚡⚡⚡ | ⭐⭐⭐ |

---

## 🐛 Solución de Problemas

### Ollama no responde
```bash
# Verificar que Ollama está corriendo
ollama list

# Si no está corriendo, iniciarlo
ollama serve
```

### Error de conexión WebSocket
- Verifica que el backend esté corriendo en el puerto 8000
- Revisa la consola del navegador para más detalles

### Modelos lentos
- Usa modelos más pequeños (gemma3, phi4)
- Cierra otras aplicaciones que usen GPU
- Considera usar menos jugadores

---

## 📝 Licencia

MIT License - Usa, modifica y distribuye libremente.

---

## 🙏 Créditos

- Inspirado en juegos de deducción social como "Spyfall" y "Palabra Secreta"
- Construido con FastAPI, React, Vite, Tailwind CSS
- Modelos de IA servidos por Ollama
