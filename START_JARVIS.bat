@echo off
title JARVIS - Assistant Vocal Windows
color 0A

echo.
echo  ============================================
echo   JARVIS - Just A Rather Very Intelligent System
echo   Assistant Vocal Windows Complet
echo  ============================================
echo.

:: Vérifie Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

:: Active l'environnement virtuel si présent
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] Environnement virtuel active
) else (
    echo [INFO] Pas d'environnement virtuel, utilisation de Python global
)

:: Vérifie les dépendances
echo [INFO] Verification des dependances...
pip install -q edge-tts pyaudio openai-whisper fastapi uvicorn 2>nul

echo.
echo [INFO] Demarrage de JARVIS...
echo [INFO] Dites "Jarvis" suivi de votre commande
echo [INFO] Ctrl+C pour arreter
echo.

:: Lance JARVIS
python -m whisperflow.jarvis.jarvis_server

pause
