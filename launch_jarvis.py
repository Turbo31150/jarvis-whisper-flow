#!/usr/bin/env python3
"""
JARVIS Launch — Demarrage complet du systeme voice + cluster + Telegram.

Usage:
    python launch_jarvis.py              # Lance tout (voice + health check)
    python launch_jarvis.py --check      # Health check seulement
    python launch_jarvis.py --voice      # Voice only (micro + Whisper + TTS)
    python launch_jarvis.py --test       # Test rapide du pipeline
"""

import asyncio
import json
import sys
import os
import time
import argparse

# Fix Windows encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


BANNER = """
  ============================================
   JARVIS WhisperFlow v2.0 — Full Pipeline
   Voice + Cluster (M1/OL1) + 140 Commands
   27 Skills | 4 Agents | 395 Cowork Scripts
  ============================================
"""


async def health_check():
    """Check all services."""
    print("\n  Health Check")
    print("  " + "-" * 40)

    checks = {}

    # M1
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("http://127.0.0.1:1234/api/v1/models")
            data = r.json()
            loaded = [m for m in data.get("data", data.get("models", [])) if m.get("loaded_instances")]
            checks["M1"] = f"OK ({len(loaded)} modeles)" if loaded else "LOADED=0"
    except Exception as e:
        checks["M1"] = f"OFFLINE ({e})"

    # OL1
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get("http://127.0.0.1:11434/api/tags")
            data = r.json()
            count = len(data.get("models", []))
            checks["OL1"] = f"OK ({count} modeles)"
    except Exception as e:
        checks["OL1"] = f"OFFLINE ({e})"

    # OpenClaw
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get("http://127.0.0.1:18789/health")
            checks["OpenClaw"] = "OK (port 18789)" if r.status_code == 200 else f"HTTP {r.status_code}"
    except Exception as e:
        checks["OpenClaw"] = f"OFFLINE ({e})"

    # Commander
    try:
        from whisperflow.jarvis.commander import Commander
        c = Commander()
        cmd = c.parse("ouvre chrome")
        checks["Commander"] = f"OK (140 intents)" if cmd else "FAIL"
    except Exception as e:
        checks["Commander"] = f"FAIL ({e})"

    # TTS
    try:
        from whisperflow.jarvis.tts_engine import TTSEngine
        checks["TTS"] = "OK (fr-FR-DeniseNeural)"
    except Exception as e:
        checks["TTS"] = f"FAIL ({e})"

    # Cowork
    cowork_path = "F:/BUREAU/jarvis-cowork/dev"
    if os.path.exists(cowork_path):
        count = len([f for f in os.listdir(cowork_path) if f.endswith(".py")])
        checks["Cowork"] = f"OK ({count} scripts)"
    else:
        checks["Cowork"] = "NOT FOUND"

    for name, status in checks.items():
        icon = "OK" if "OK" in status else "!!"
        print(f"  [{icon}] {name:12s}: {status}")

    print()
    return all("OK" in v for v in checks.values())


async def test_pipeline():
    """Quick pipeline test: Commander + Cluster."""
    print("\n  Pipeline Test")
    print("  " + "-" * 40)

    from whisperflow.jarvis.commander import Commander
    from whisperflow.jarvis.cluster_bridge import cluster_race

    c = Commander()

    tests = [
        ("ouvre chrome", "app_launch"),
        ("volume a 50", "system_volume_set"),
        ("quelle heure", "system_time"),
        ("google python", "web_google"),
    ]

    for text, expected in tests:
        cmd = c.parse(text)
        ok = cmd and cmd.intent == expected
        print(f"  {'OK' if ok else 'FAIL'} '{text}' -> {cmd.intent if cmd else 'None'}")

    # Test cluster
    print("\n  Cluster Race Test:")
    t0 = time.time()
    reply, agent = await cluster_race("Bonjour, ca va?")
    lat = time.time() - t0
    if reply:
        print(f"  OK [{agent}] {lat:.2f}s -> {reply[:80]}")
    else:
        print(f"  FAIL (no response in {lat:.2f}s)")

    print()


async def main():
    parser = argparse.ArgumentParser(description="JARVIS Launch")
    parser.add_argument("--check", action="store_true", help="Health check only")
    parser.add_argument("--test", action="store_true", help="Quick pipeline test")
    parser.add_argument("--voice", action="store_true", help="Voice mode (micro + Whisper)")
    args = parser.parse_args()

    print(BANNER)

    if args.check:
        await health_check()
        return

    if args.test:
        await health_check()
        await test_pipeline()
        return

    # Full launch: health check then voice
    all_ok = await health_check()
    if not all_ok:
        print("  ATTENTION: Certains services sont offline.")
        print("  Le systeme fonctionnera avec les services disponibles.\n")

    await test_pipeline()

    if args.voice or not (args.check or args.test):
        print("  Demarrage du mode vocal...")
        print("  Dites 'Jarvis' suivi de votre commande.\n")
        from whisperflow.jarvis.jarvis_server import main as server_main
        await server_main()


if __name__ == "__main__":
    asyncio.run(main())
