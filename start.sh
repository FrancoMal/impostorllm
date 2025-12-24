#!/bin/bash

echo "========================================"
echo "  Impostor LLM - Game Server"
echo "========================================"
echo

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[!] Ollama no esta corriendo. Por favor inicia Ollama primero."
    echo "    Ejecuta: ollama serve"
    exit 1
fi

# Start backend
echo "[1/2] Iniciando backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "    Creando entorno virtual..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "[2/2] Iniciando frontend..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "    Instalando dependencias..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!

echo
echo "========================================"
echo "  Servidores iniciados!"
echo "  - Backend: http://localhost:8000"
echo "  - Frontend: http://localhost:5173"
echo "========================================"
echo
echo "Abre http://localhost:5173 en tu navegador"
echo "Presiona Ctrl+C para detener los servidores"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
