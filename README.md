# JARVIS Whisper-Flow — Complete Voice Assistant

> **EN** | [FR](#version-française)
>
> ![Python](https://img.shields.io/badge/python-3.11+-green)
> ![Platform](https://img.shields.io/badge/platform-Windows-blue)
> ![License](https://img.shields.io/badge/license-MIT-brightgreen)
> ![Whisper](https://img.shields.io/badge/whisper-faster--whisper_large--v3-orange)
>
> Complete Windows voice assistant powered by Whisper-Flow — wake word detection, GPU-accelerated STT, multi-AI dispatch, and TTS response. Part of the [JARVIS ecosystem](https://github.com/Turbo31150/jarvis-linux).
>
> ---
>
> ## Table of Contents
>
> 1. [Overview](#overview)
> 2. 2. [Architecture](#architecture)
>    3. 3. [Features](#features)
>       4. 4. [Voice Pipeline](#voice-pipeline)
>          5. 5. [File Structure](#file-structure)
>             6. 6. [Installation](#installation)
>                7. 7. [Configuration](#configuration)
>                   8. 8. [Usage](#usage)
>                      9. 9. [Integration with JARVIS](#integration-with-jarvis)
>                         10. 10. [Related Repos](#related-repos)
>                             11. 11. [Version Française](#version-française)
>                                
>                                 12. ---
>                                
>                                 13. ## Overview
>                                
>                                 14. JARVIS Whisper-Flow is a complete voice assistant for Windows that integrates:
> - **Wake word detection** via Porcupine (keyword: "Jarvis")
> - - **Speech-to-Text** via faster-whisper (large-v3-turbo, GPU CUDA)
>   - - **Multi-AI dispatch** to LM Studio, Ollama, Gemini, or Claude
>     - - **Text-to-Speech** via edge-tts (fr-FR-DeniseNeural) or espeak-ng
>       - - **WebSocket streaming** for real-time transcription
>        
>         - ---
>
> ## Architecture
>
> ```
> Microphone (Windows sounddevice)
>          |
> [Porcupine Wake Word "Jarvis"]
>     sensitivity: 0.6-0.7
>     custom .ppn model
>          |
> [5s Audio Recording]
>     16kHz, 16-bit, mono
>          |
> [WhisperFlow STT]
>     faster-whisper large-v3-turbo
>     GPU CUDA acceleration
>          |
> [Voice Correction]
>     2,628 aliases (etoile.db)
>     "play music" → "play_music"
>          |
> [Command Filter]
>     WHITELIST: direct exec
>     GREYLIST: user confirmation
>     BLACKLIST: refused (rm -rf, etc.)
>          |
> [AI Dispatch]
>     LM Studio (local GPU)
>     Ollama (local/cloud)
>     Gemini API
>     Claude API
>          |
> [TTS Response]
>     edge-tts fr-FR-DeniseNeural
>     espeak-ng (offline fallback)
>     Piper (if installed)
>          |
> Speaker (Windows audio)
> ```
>
> ---
>
> ## Features
>
> - **Wake word**: "Jarvis" — Porcupine pvporcupine, sensitivity 0.6-0.7
> - - **STT**: faster-whisper large-v3-turbo — GPU accelerated, French + English
>   - - **Voice correction**: 2,628 aliases for phonetic matching
>     - - **Security filter**: 3-level whitelist/greylist/blacklist
>       - - **Multi-AI**: Routes to best available AI (local GPU first, cloud fallback)
>         - - **TTS**: edge-tts (neural) or espeak-ng (offline)
>           - - **Streaming**: Real-time WebSocket transcription
>             - - **Windows native**: sounddevice, Windows audio, portable exe support
>              
>               - ---
>
> ## Voice Pipeline
>
> | Step | Component | File |
> |------|-----------|------|
> | 1. Wake word | Porcupine detection | `wakeword_porcupine.py` |
> | 2. Recording | sounddevice 5s | `voice_engine.py` |
> | 3. STT | faster-whisper CUDA | `transcriber.py` |
> | 4. Correction | 2,628 alias lookup | `voice_correction.py` |
> | 5. Filter | 3-level security | `command_filter.py` |
> | 6. Dispatch | Multi-AI routing | `voice_hub.py` |
> | 7. TTS | edge-tts / espeak | `tts_engine.py` |
> | 8. Streaming | WebSocket real-time | `streaming.py` |
>
> ---
>
> ## File Structure
>
> ```
> jarvis-whisper-flow/
> ├── voice_engine.py          # Main voice pipeline (wake word + record + dispatch)
> ├── voice_hub.py             # Flask server (/voice/audio, /voice/text, /voice/status)
> ├── wakeword_porcupine.py    # Porcupine wake word detection
> ├── command_filter.py        # Security filter (whitelist/greylist/blacklist)
> ├── voice_correction.py      # Voice correction (2,415 lines, 2,628 aliases)
> ├── tts_engine.py            # Text-to-Speech (espeak-ng / edge-tts)
> ├── voice_commands.json      # Voice → MCP action mapping (140+ commands)
> ├── transcriber.py           # Whisper transcription engine
> ├── streaming.py             # WebSocket streaming (real-time)
> ├── fast_server.py           # Fast HTTP server
> ├── whisperflow_client.py    # WebSocket client (transcribe_file, transcribe_stream)
> └── whisperflow_mcp.py       # MCP server (port 8082, 2 tools)
> ```
>
> ---
>
> ## Installation
>
> ### Prerequisites
> - Windows 10/11
> - - Python 3.11+
>   - - NVIDIA GPU (recommended) with CUDA drivers
>     - - Picovoice account (free) for Porcupine wake word
>       - - HuggingFace account for Whisper models
>        
>         - ```bash
>           git clone https://github.com/Turbo31150/jarvis-whisper-flow.git
>           cd jarvis-whisper-flow
>
>           pip install faster-whisper pvporcupine sounddevice edge-tts flask
>           ```
>
> ---
>
> ## Configuration
>
> ```bash
> # .env file
> PV_ACCESS_KEY=your_picovoice_key    # Porcupine wake word
> WAKEWORD_PATH=jarvis_windows.ppn    # Custom wake word model
> HF_TOKEN=your_huggingface_token     # Whisper model download
>
> # Optional AI backends
> LM_STUDIO_URL=http://127.0.0.1:1234
> OLLAMA_URL=http://127.0.0.1:11434
> ANTHROPIC_API_KEY=sk-ant-...
> GEMINI_API_KEY=...
> ```
>
> ---
>
> ## Usage
>
> ```bash
> # Start full voice assistant
> python voice_engine.py
>
> # Start voice hub (REST API)
> python voice_hub.py
> # → POST /voice/audio  (audio file)
> # → POST /voice/text   (text command)
> # → GET  /voice/status
>
> # Start STT streaming server
> python fast_server.py
>
> # Transcribe a file
> python whisperflow_client.py transcribe audio.wav
>
> # MCP server (port 8082)
> python whisperflow_mcp.py
> ```
>
> ### Voice Commands Examples
> - *"Jarvis, what's the Bitcoin price?"*
> - - *"Jarvis, run system health check"*
>   - - *"Jarvis, open my trading dashboard"*
>     - - *"Jarvis, what's the GPU temperature?"*
>       - - *"Jarvis, stop all services"*
>        
>         - ---
>
> ## Integration with JARVIS
>
> When used with [jarvis-linux](https://github.com/Turbo31150/jarvis-linux):
>
> - **MCP tools**: `whisperflow_mcp.py` exposes `transcribe` and `status` tools (port 8082, Bearer `wf-jarvis-2026`)
> - - **Docker**: `vocal-whisper` container (port 18001:8000)
>   - - **Systemd**: `jarvis-voice.service` + `jarvis-whisper.service`
>     - - **WebSocket**: Connects to `jarvis-ws :9742` for response streaming
>       - - **Database**: Voice aliases stored in `etoile.db` (2,628 entries)
>        
>         - ---
>
> ## Related Repos
>
> | Repo | Description |
> |------|-------------|
> | [jarvis-linux](https://github.com/Turbo31150/jarvis-linux) | Main JARVIS repo — full Linux deployment |
> | [JARVIS-CLUSTER](https://github.com/Turbo31150/JARVIS-CLUSTER) | Multi-node cluster infrastructure |
> | [jarvis-cowork](https://github.com/Turbo31150/jarvis-cowork) | 249 autonomous development scripts |
> | [gemini-live-trading-agent](https://github.com/Turbo31150/gemini-live-trading-agent) | Voice trading via Gemini Live |
>
> ---
>
> *Author: Turbo31150 | Platform: Windows | STT: faster-whisper large-v3-turbo | License: MIT | March 2026*
>
> ---
> ---
>
> # Version Française
>
> > [EN](#jarvis-whisper-flow--complete-voice-assistant) | **FR**
> >
> > ![Python](https://img.shields.io/badge/python-3.11+-green)
> > ![Plateforme](https://img.shields.io/badge/plateforme-Windows-blue)
> > ![Licence](https://img.shields.io/badge/licence-MIT-brightgreen)
> > ![Whisper](https://img.shields.io/badge/whisper-faster--whisper_large--v3-orange)
> >
> > Assistant vocal complet pour Windows basé sur Whisper-Flow — détection de mot-réveil, STT accéléré GPU, dispatch multi-IA, et réponse TTS. Fait partie de l'[écosystème JARVIS](https://github.com/Turbo31150/jarvis-linux).
> >
> > ---
> >
> > ## Table des matières FR
> >
> > 1. [Vue d'ensemble](#vue-densemble)
> > 2. 2. [Architecture](#architecture-fr)
> >    3. 3. [Fonctionnalités](#fonctionnalités)
> >       4. 4. [Pipeline vocal](#pipeline-vocal-fr)
> >          5. 5. [Structure des fichiers](#structure-des-fichiers)
> >             6. 6. [Installation](#installation-fr)
> >                7. 7. [Configuration](#configuration-fr)
> >                   8. 8. [Utilisation](#utilisation-fr)
> >                      9. 9. [Intégration avec JARVIS](#intégration-avec-jarvis-fr)
> >                         10. 10. [Repos liés](#repos-liés-fr)
> >                            
> >                             11. ---
> >                            
> >                             12. ## Vue d'ensemble
> >                            
> >                             13. JARVIS Whisper-Flow est un assistant vocal complet pour Windows qui intègre :
> > - **Détection de mot-réveil** via Porcupine (mot-clé : "Jarvis")
> > - - **Reconnaissance vocale** via faster-whisper (large-v3-turbo, GPU CUDA)
> >   - - **Dispatch multi-IA** vers LM Studio, Ollama, Gemini ou Claude
> >     - - **Synthèse vocale** via edge-tts (fr-FR-DeniseNeural) ou espeak-ng
> >       - - **Streaming WebSocket** pour transcription en temps réel
> >        
> >         - ---
> >
> > ## Architecture FR
> >
> > ```
> > Microphone (Windows sounddevice)
> >          |
> > [Porcupine Wake Word "Jarvis"]
> >     sensibilité : 0.6-0.7
> >     modèle .ppn personnalisé
> >          |
> > [Enregistrement 5s]
> >     16kHz, 16-bit, mono
> >          |
> > [WhisperFlow STT]
> >     faster-whisper large-v3-turbo
> >     accélération GPU CUDA
> >          |
> > [Correction Vocale]
> >     2 628 alias (etoile.db)
> >     "met la musique" → "play_music"
> >          |
> > [Filtre de Commandes]
> >     WHITELIST : exec directe
> >     GREYLIST  : confirmation utilisateur
> >     BLACKLIST : refusé (rm -rf, etc.)
> >          |
> > [Dispatch IA]
> >     LM Studio (GPU local)
> >     Ollama (local/cloud)
> >     Gemini API
> >     Claude API
> >          |
> > [Réponse TTS]
> >     edge-tts fr-FR-DeniseNeural
> >     espeak-ng (fallback hors ligne)
> >     Piper (si installé)
> >          |
> > Haut-parleur (audio Windows)
> > ```
> >
> > ---
> >
> > ## Fonctionnalités
> >
> > - **Mot-réveil** : "Jarvis" — Porcupine pvporcupine, sensibilité 0.6-0.7
> > - - **STT** : faster-whisper large-v3-turbo — GPU accéléré, Français + Anglais
> >   - - **Correction vocale** : 2 628 alias pour correspondance phonétique
> >     - - **Filtre de sécurité** : 3 niveaux whitelist/greylist/blacklist
> >       - - **Multi-IA** : Route vers la meilleure IA disponible (GPU local en priorité, cloud en fallback)
> >         - - **TTS** : edge-tts (neural) ou espeak-ng (hors ligne)
> >           - - **Streaming** : Transcription WebSocket en temps réel
> >             - - **Windows natif** : sounddevice, audio Windows, support exe portable
> >              
> >               - ---
> >
> > ## Pipeline vocal FR
> >
> > | Étape | Composant | Fichier |
> > |-------|-----------|---------|
> > | 1. Mot-réveil | Détection Porcupine | `wakeword_porcupine.py` |
> > | 2. Enregistrement | sounddevice 5s | `voice_engine.py` |
> > | 3. STT | faster-whisper CUDA | `transcriber.py` |
> > | 4. Correction | Lookup 2 628 alias | `voice_correction.py` |
> > | 5. Filtre | Sécurité 3 niveaux | `command_filter.py` |
> > | 6. Dispatch | Routage multi-IA | `voice_hub.py` |
> > | 7. TTS | edge-tts / espeak | `tts_engine.py` |
> > | 8. Streaming | WebSocket temps réel | `streaming.py` |
> >
> > ---
> >
> > ## Structure des fichiers
> >
> > ```
> > jarvis-whisper-flow/
> > ├── voice_engine.py          # Pipeline vocal principal (wake word + record + dispatch)
> > ├── voice_hub.py             # Serveur Flask (/voice/audio, /voice/text, /voice/status)
> > ├── wakeword_porcupine.py    # Détection wake word Porcupine
> > ├── command_filter.py        # Filtre sécurité (whitelist/greylist/blacklist)
> > ├── voice_correction.py      # Correction vocale (2 415 lignes, 2 628 alias)
> > ├── tts_engine.py            # Text-to-Speech (espeak-ng / edge-tts)
> > ├── voice_commands.json      # Mapping voix → actions MCP (140+ commandes)
> > ├── transcriber.py           # Moteur de transcription Whisper
> > ├── streaming.py             # Streaming WebSocket (temps réel)
> > ├── fast_server.py           # Serveur HTTP rapide
> > ├── whisperflow_client.py    # Client WebSocket (transcribe_file, transcribe_stream)
> > └── whisperflow_mcp.py       # Serveur MCP (port 8082, 2 outils)
> > ```
> >
> > ---
> >
> > ## Installation FR
> >
> > ### Prérequis
> > - Windows 10/11
> > - - Python 3.11+
> >   - - GPU NVIDIA (recommandé) avec drivers CUDA
> >     - - Compte Picovoice (gratuit) pour le wake word Porcupine
> >       - - Compte HuggingFace pour les modèles Whisper
> >        
> >         - ```bash
> >           git clone https://github.com/Turbo31150/jarvis-whisper-flow.git
> >           cd jarvis-whisper-flow
> >
> >           pip install faster-whisper pvporcupine sounddevice edge-tts flask
> >           ```
> >
> > ---
> >
> > ## Configuration FR
> >
> > ```bash
> > # Fichier .env
> > PV_ACCESS_KEY=votre_cle_picovoice    # Wake word Porcupine
> > WAKEWORD_PATH=jarvis_windows.ppn     # Modèle wake word personnalisé
> > HF_TOKEN=votre_token_huggingface     # Téléchargement modèle Whisper
> >
> > # Backends IA optionnels
> > LM_STUDIO_URL=http://127.0.0.1:1234
> > OLLAMA_URL=http://127.0.0.1:11434
> > ANTHROPIC_API_KEY=sk-ant-...
> > GEMINI_API_KEY=...
> > ```
> >
> > ---
> >
> > ## Utilisation FR
> >
> > ```bash
> > # Démarrer l'assistant vocal complet
> > python voice_engine.py
> >
> > # Démarrer le hub vocal (API REST)
> > python voice_hub.py
> > # → POST /voice/audio  (fichier audio)
> > # → POST /voice/text   (commande texte)
> > # → GET  /voice/status
> >
> > # Démarrer le serveur de streaming STT
> > python fast_server.py
> >
> > # Transcrire un fichier
> > python whisperflow_client.py transcribe audio.wav
> >
> > # Serveur MCP (port 8082)
> > python whisperflow_mcp.py
> > ```
> >
> > ### Exemples de commandes vocales
> > - *"Jarvis, quel est le prix du Bitcoin ?"*
> > - - *"Jarvis, lance le health check système"*
> >   - - *"Jarvis, ouvre mon dashboard de trading"*
> >     - - *"Jarvis, quelle est la température du GPU ?"*
> >       - - *"Jarvis, arrête tous les services"*
> >        
> >         - ---
> >
> > ## Intégration avec JARVIS FR
> >
> > En utilisation avec [jarvis-linux](https://github.com/Turbo31150/jarvis-linux) :
> >
> > - **Outils MCP** : `whisperflow_mcp.py` expose `transcribe` et `status` (port 8082, Bearer `wf-jarvis-2026`)
> > - - **Docker** : Conteneur `vocal-whisper` (port 18001:8000)
> >   - - **Systemd** : `jarvis-voice.service` + `jarvis-whisper.service`
> >     - - **WebSocket** : Se connecte à `jarvis-ws :9742` pour le streaming des réponses
> >       - - **Base de données** : Alias vocaux stockés dans `etoile.db` (2 628 entrées)
> >        
> >         - ---
> >
> > ## Repos liés FR
> >
> > | Repo | Description |
> > |------|-------------|
> > | [jarvis-linux](https://github.com/Turbo31150/jarvis-linux) | Repo principal JARVIS — déploiement Linux complet |
> > | [JARVIS-CLUSTER](https://github.com/Turbo31150/JARVIS-CLUSTER) | Infrastructure cluster multi-nœuds |
> > | [jarvis-cowork](https://github.com/Turbo31150/jarvis-cowork) | 249 scripts de développement autonome |
> > | [gemini-live-trading-agent](https://github.com/Turbo31150/gemini-live-trading-agent) | Trading vocal via Gemini Live |
> >
> > ---
> >
> > *Auteur : Turbo31150 | Plateforme : Windows | STT : faster-whisper large-v3-turbo | Licence : MIT | Mars 2026*
