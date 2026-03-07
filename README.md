# JARVIS WhisperFlow - Assistant Vocal Windows Complet

Systeme vocal temps reel base sur Whisper-Flow, integre avec OpenClaw (orchestrateur IA) et un cluster GPU local.

## Architecture

```
Utilisateur (voix/texte)
    |
    +---> [Telegram] ---> OpenClaw Gateway (port 18789)
    |                         |
    |                         +---> M1/qwen3-8b (LM Studio, port 1234)
    |                         +---> Outils: browser, exec, fichiers, cron...
    |                         +---> TTS Denise (si vocal recu)
    |                         |
    |                         +---> Reponse texte + vocal Telegram
    |
    +---> [WhisperFlow] ---> Micro local → Whisper STT temps reel
                              |
                              +---> Wake word "Jarvis"
                              +---> Commander (140 commandes locales)
                              +---> Si inconnu → M1/qwen3-8b (LLM)
                              +---> TTS fr-FR-DeniseNeural (Edge TTS)
```

## Composants

| Composant | Role | Port/Config |
|-----------|------|-------------|
| **WhisperFlow** | STT temps reel (micro local) | Capture audio directe |
| **JARVIS Commander** | 140 commandes vocales FR | Regex pattern matching |
| **OpenClaw Gateway** | Orchestrateur IA + outils | ws://127.0.0.1:18789 |
| **M1 (LM Studio)** | LLM qwen3-8b (46 tok/s) | http://127.0.0.1:1234 |
| **OL1 (Ollama)** | Fallback rapide qwen3:1.7b | http://127.0.0.1:11434 |
| **TTS Engine** | Edge TTS fr-FR-DeniseNeural | Lecture locale + Telegram |
| **Telegram Bot** | Interface mobile @turboSSebot | Via OpenClaw plugin |

## Installation rapide (Windows)

### Prerequis
- Python 3.10+ avec pip
- Node.js 20+ (pour OpenClaw)
- LM Studio avec qwen3-8b charge
- Micro fonctionnel

### 1. Cloner et installer WhisperFlow

```bash
git clone https://github.com/Turbo31150/jarvis-whisper-flow.git
cd jarvis-whisper-flow
pip install -r requirements.txt
```

### 2. Installer OpenClaw

```bash
npm install -g openclaw
openclaw doctor
```

### 3. Configurer OpenClaw

```bash
# Modele principal: M1 local
openclaw config set agents.defaults.model.primary "lm-m1/qwen3-8b"

# Activer Telegram
openclaw plugins enable telegram
openclaw channels add --channel telegram --token "VOTRE_BOT_TOKEN"

# Workspace JARVIS cowork
openclaw config set agents.defaults.workspace "F:/BUREAU/jarvis-cowork"
```

Ajouter le provider M1 dans `~/.openclaw/openclaw.json` :

```json
{
  "models": {
    "providers": {
      "lm-m1": {
        "baseUrl": "http://127.0.0.1:1234/v1",
        "api": "openai-completions",
        "models": [{
          "id": "qwen3-8b",
          "name": "Qwen3 8B (M1 LOCAL)",
          "reasoning": false,
          "input": ["text"],
          "contextWindow": 32768,
          "cost": {"input": 0, "output": 0}
        }]
      }
    }
  }
}
```

### 4. Lancer le systeme

```bash
# Terminal 1: OpenClaw Gateway
openclaw gateway --port 18789

# Terminal 2: WhisperFlow (ecoute micro)
cd F:\BUREAU\jarvis-whisper-flow
python -m whisperflow.jarvis
```

### 5. Tache planifiee Windows (demarrage auto)

WhisperFlow se lance automatiquement au login via la tache `JARVIS_WhisperFlow`.

Creation manuelle :
```bash
schtasks /Create /TN "JARVIS_WhisperFlow" /TR "cmd /C \"cd /d F:\\BUREAU\\jarvis-whisper-flow && pythonw -m whisperflow.jarvis\"" /SC ONLOGON /RL HIGHEST /F /DELAY 0000:30
```

## Commandes vocales (140+)

Dites **"Jarvis"** suivi de la commande :

### Applications
- "Jarvis ouvre Chrome" / "Jarvis ferme Notepad"
- "Jarvis lance le terminal" / "Jarvis ouvre Word"

### Systeme
- "Jarvis monte le volume" / "Jarvis volume a 50"
- "Jarvis luminosite a 80" / "Jarvis batterie"
- "Jarvis quelle heure" / "Jarvis quel jour"

### Web
- "Jarvis google intelligence artificielle"
- "Jarvis youtube tutoriel Python"
- "Jarvis wikipedia machine learning"

### Fichiers
- "Jarvis cree un fichier test" / "Jarvis cherche rapport"
- "Jarvis ouvre telechargements"

### Dictee
- "Jarvis mode dictee" (tout est tape au clavier)
- "Arrete la dictee" (retour mode commande)

### Questions libres (via M1/qwen3-8b)
- "Jarvis c'est quoi le bitcoin"
- "Jarvis explique le machine learning"
- Toute question non reconnue comme commande locale

## Integration OpenClaw + JARVIS Cowork

OpenClaw utilise le workspace `jarvis-cowork` (438 scripts) pour :
- Execution de scripts systeme (GPU, disque, reseau, processus...)
- Trading (scan, signaux, backtests)
- Dominos/pipelines (routine matin, scan complet, mode travail...)
- Navigation browser (Comet/Chrome/Edge)
- Gestion fenetres multi-ecrans

### Scripts cowork disponibles via Telegram

```
/status    → Etat du systeme
/health    → Health check cluster
/gpu       → Temperatures GPU
/trading   → Signaux trading
/scan      → Scan marche crypto
/domino    → Lancer un pipeline
```

## Configuration TTS

Voix par defaut: `fr-FR-DeniseNeural` (Edge TTS, haute qualite).

Le texte est nettoye avant lecture :
- Pas de ponctuation, symboles, code blocks
- Pas d'URLs ni de markdown
- Lecture naturelle en francais

Modifier dans `whisperflow/jarvis/config.py` :
```python
"tts_voice": "fr-FR-DeniseNeural"  # ou fr-FR-HenriNeural
```

## Fichiers cles

```
whisperflow/
  jarvis/
    jarvis_server.py    # Point d'entree (micro → Whisper → JARVIS)
    jarvis_core.py      # Orchestrateur (Commander + Skills + M1 fallback)
    commander.py        # Parseur commandes vocales (140 patterns)
    config.py           # Configuration globale
    tts_engine.py       # TTS Edge/pyttsx3 avec nettoyage texte
    wake_word.py        # Detection "Jarvis" (exact + fuzzy)
    skills/             # 25+ skills (apps, systeme, fichiers, web, media...)
    agents/             # 4 agents (dictation, search, automation, navigation)
  streaming.py          # TranscribeSession (windowing audio)
  transcriber.py        # Whisper model loading + transcription
  audio/microphone.py   # Capture PyAudio 16kHz mono int16
```

## Cluster IA

| Noeud | Host | Modele | Vitesse |
|-------|------|--------|---------|
| M1 | 127.0.0.1:1234 | qwen3-8b | 46 tok/s |
| OL1 | 127.0.0.1:11434 | qwen3:1.7b | 84 tok/s |
| M2 | 192.168.1.26:1234 | deepseek-r1 | 44 tok/s |
| M3 | 192.168.1.113:1234 | deepseek-r1 | 33 tok/s |

## Licence

MIT
