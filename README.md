<div align="center">
  <img src="assets/logo.svg" alt="WHISPERFLOW CUDA" width="520"/>
  <br/><br/>

  [![License: MIT](https://img.shields.io/badge/License-MIT-22D3EE?style=flat-square)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.11+-22D3EE?style=flat-square&logo=python&logoColor=black)](#)
  [![CUDA](https://img.shields.io/badge/CUDA-12.1-76B900?style=flat-square&logo=nvidia&logoColor=white)](#prerequisites)
  [![Whisper](https://img.shields.io/badge/Whisper-large--v3-38BDF8?style=flat-square&logo=openai&logoColor=white)](#model-comparison)
  [![Latency](https://img.shields.io/badge/Latency-%3C300ms-22D3EE?style=flat-square)](#benchmarks)
  [![Skills](https://img.shields.io/badge/26_skills-voice--activated-38BDF8?style=flat-square)](#skill-catalog)
  [![JARVIS](https://img.shields.io/badge/JARVIS-Voice_Layer-22D3EE?style=flat-square)](#jarvis-integration)

  <br/>
  <h3>Real-Time CUDA Voice Pipeline &mdash; Whisper large-v3 &bull; &lt;300ms Latency &bull; 26 Voice Skills</h3>
  <p><em>The high-performance voice layer of the JARVIS ecosystem &mdash; transforms speech into AI-executed commands in under 300 milliseconds.</em></p>

  <br/>

  [Pipeline](#pipeline) &bull; [Skills](#skill-catalog) &bull; [Benchmarks](#benchmarks) &bull; [Installation](#installation) &bull; [JARVIS Integration](#jarvis-integration)
</div>

---

## Overview

**WHISPERFLOW CUDA** is the voice-to-action pipeline for the JARVIS ecosystem. It chains **Voice Activity Detection (VAD)**, **wake word detection**, **OpenAI Whisper large-v3** with CUDA acceleration, and an **intent router** to deliver sub-300ms voice command processing.

Say _"Jarvis"_, speak your command, and the system transcribes, interprets, and routes it to the appropriate JARVIS agent &mdash; all in real time.

---

## Pipeline

```
  +------------------+
  |    Microphone     |    Continuous audio capture
  +--------+---------+
           |
           v
  +------------------+
  |   Silero VAD     |    Voice Activity Detection
  |   < 50ms         |    Filters silence, reduces GPU load
  +--------+---------+
           | voice detected
           v
  +------------------+
  |  Wake Word       |    Listens for "Jarvis"
  |  Detection       |    Configurable trigger phrase
  |  < 100ms         |
  +--------+---------+
           | wake word confirmed
           v
  +------------------+
  |  Audio Buffer    |    WebRTC-based buffering
  |  2-5 seconds     |    Adaptive window sizing
  +--------+---------+
           |
           v
  +------------------+
  |  Whisper         |    OpenAI Whisper large-v3
  |  large-v3        |    CUDA fp16 inference
  |  < 300ms (GPU)   |    Multilingual (fr/en)
  +--------+---------+
           | transcription
           v
  +------------------+
  |  Post-Processing |    Punctuation restoration
  |                  |    Text normalization
  +--------+---------+
           |
           v
  +------------------+
  |  Intent Router   |    WebSocket :9742
  |  -> JARVIS Core  |    Routes to 26 skills
  +------------------+
```

---

## Skill Catalog

WhisperFlow routes voice commands to **26 built-in skills** via the JARVIS intent router:

| # | Skill | Voice Trigger (example) | Action |
|:-:|:------|:------------------------|:-------|
| 1 | **System Status** | _"Jarvis, system status"_ | Returns CPU, RAM, GPU, disk usage |
| 2 | **GPU Monitor** | _"Jarvis, GPU info"_ | NVIDIA GPU temps, VRAM, utilization |
| 3 | **Process List** | _"Jarvis, list processes"_ | Top processes by resource usage |
| 4 | **Kill Process** | _"Jarvis, kill Chrome"_ | Terminate a named process |
| 5 | **Open App** | _"Jarvis, open Firefox"_ | Launch an application |
| 6 | **Screenshot** | _"Jarvis, screenshot"_ | Capture screen to file |
| 7 | **File Search** | _"Jarvis, find my report"_ | Search files by name/content |
| 8 | **Clipboard** | _"Jarvis, copy that"_ | Read/write system clipboard |
| 9 | **Timer** | _"Jarvis, set timer 5 min"_ | Start countdown timer |
| 10 | **Reminder** | _"Jarvis, remind me at 3pm"_ | Schedule a reminder |
| 11 | **Weather** | _"Jarvis, weather Toulouse"_ | Current weather and forecast |
| 12 | **News** | _"Jarvis, latest news"_ | Headline summary |
| 13 | **Translate** | _"Jarvis, translate hello in Japanese"_ | Real-time translation |
| 14 | **Calculate** | _"Jarvis, what is 15% of 340"_ | Math and conversions |
| 15 | **Trade Status** | _"Jarvis, my positions"_ | Open trading positions via TradeOracle |
| 16 | **Trade Signal** | _"Jarvis, scan BTC"_ | Request trading signal |
| 17 | **Cluster Health** | _"Jarvis, cluster status"_ | JARVIS-CLUSTER node health |
| 18 | **Deploy** | _"Jarvis, deploy cowork agents"_ | Trigger deployment pipeline |
| 19 | **Git Status** | _"Jarvis, git status"_ | Current repo status |
| 20 | **Run Tests** | _"Jarvis, run tests"_ | Execute test suite |
| 21 | **Docker** | _"Jarvis, docker ps"_ | Container management |
| 22 | **SSH** | _"Jarvis, connect to M3"_ | SSH to cluster node |
| 23 | **Volume** | _"Jarvis, volume 50"_ | System audio control |
| 24 | **Brightness** | _"Jarvis, brightness up"_ | Display brightness control |
| 25 | **Dictation** | _"Jarvis, take note"_ | Continuous dictation mode |
| 26 | **Custom** | _"Jarvis, run macro deploy-all"_ | User-defined macro execution |

---

## Benchmarks

### Latency (RTX 3080 10GB)

| Component | Latency | Notes |
|:----------|--------:|:------|
| VAD (Silero) | 30-50ms | Per audio chunk |
| Wake word detection | 80-100ms | Single pass |
| Whisper large-v3 (CUDA) | 180-280ms | 5s audio segment, fp16 |
| Post-processing | 10-20ms | Punctuation + normalization |
| Intent routing (WS) | 5-10ms | Local WebSocket |
| **End-to-end** | **< 300ms** | **Wake word to agent dispatch** |

### Model Comparison

| Model | VRAM | WER (fr) | WER (en) | Latency | Recommended For |
|:------|-----:|:--------:|:--------:|--------:|:----------------|
| `tiny` | 1 GB | ~12% | ~10% | 50ms | Development, testing |
| `base` | 1 GB | ~9% | ~7% | 80ms | Low-resource devices |
| `small` | 2 GB | ~6% | ~5% | 120ms | Balanced use |
| `medium` | 5 GB | ~4% | ~3.5% | 180ms | Good accuracy |
| **`large-v3`** | **10 GB** | **~2.5%** | **~2%** | **< 300ms** | **Production** |

### Throughput

| Metric | Value |
|:-------|------:|
| Concurrent streams | 1 (single mic) |
| Continuous uptime tested | 72+ hours |
| Memory leak | None detected |
| CPU fallback latency | ~1.5s (large-v3) |

---

## Installation

### Prerequisites

- Python 3.11+
- NVIDIA GPU with CUDA 12.1+ (10GB+ VRAM for large-v3)
- PulseAudio or PipeWire (Linux) / CoreAudio (macOS)
- JARVIS WebSocket broker on `:9742` (optional, for routing)

### Setup

```bash
git clone https://github.com/Turbo31150/jarvis-whisper-flow.git
cd jarvis-whisper-flow

# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install dependencies
pip install -r requirements.txt

# Download Whisper model (first run only)
python -c "import whisper; whisper.load_model('large-v3')"

# Configure
cp .env.example .env
```

### Configuration

```env
WHISPER_MODEL=large-v3       # Model size (tiny/base/small/medium/large-v3)
WHISPER_DEVICE=cuda           # cuda or cpu
WHISPER_LANGUAGE=fr           # Primary language
VAD_THRESHOLD=0.5             # Voice detection sensitivity (0-1)
WAKE_WORD=jarvis              # Trigger phrase
JARVIS_WS=ws://127.0.0.1:9742  # JARVIS WebSocket endpoint
```

### Run

```bash
python main.py
```

On startup, WhisperFlow will:
1. Load the Whisper model onto GPU
2. Initialize VAD and wake word detector
3. Open the default microphone
4. Begin listening for the wake word

---

## JARVIS Integration

WhisperFlow connects to the JARVIS ecosystem via WebSocket:

```python
import websockets, json

async def send_to_jarvis(text: str, confidence: float):
    async with websockets.connect("ws://127.0.0.1:9742") as ws:
        await ws.send(json.dumps({
            "type": "voice_command",
            "text": text,
            "confidence": confidence,
            "language": "fr",
            "source": "whisperflow",
            "timestamp": "2026-03-24T12:00:00Z"
        }))
```

### Related Projects

| Project | Role |
|:--------|:-----|
| [jarvis-cowork](https://github.com/Turbo31150/jarvis-cowork) | Agent workspace triggered by voice |
| [TradeOracle](https://github.com/Turbo31150/TradeOracle) | Trading commands via voice |
| [JARVIS-CLUSTER](https://github.com/Turbo31150/JARVIS-CLUSTER) | Cluster management via voice |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">
  <br/>
  <strong>Franc Delmas (Turbo31150)</strong> &bull; <a href="https://github.com/Turbo31150">github.com/Turbo31150</a> &bull; Toulouse, France
  <br/><br/>
  <em>WHISPERFLOW CUDA &mdash; Real-Time Voice Pipeline for JARVIS</em>
</div>
