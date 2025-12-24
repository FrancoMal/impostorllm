@echo off
echo ========================================
echo   Impostor LLM - Game Server
echo ========================================
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [!] Ollama no esta corriendo. Iniciando...
    start "" ollama serve
    timeout /t 3 >nul
)

REM Start backend
echo [1/2] Iniciando backend...
cd backend
if not exist venv (
    echo     Creando entorno virtual...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
start "Backend" cmd /k "python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
timeout /t 3 >nul

REM Start frontend
echo [2/2] Iniciando frontend...
cd ..\frontend
if not exist node_modules (
    echo     Instalando dependencias...
    call npm install
)
start "Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   Servidores iniciados!
echo   - Backend: http://localhost:8000
echo   - Frontend: http://localhost:5173
echo ========================================
echo.
echo Abre http://localhost:5173 en tu navegador
echo.
pause
