#!/usr/bin/env python3
"""
JARVIS Dual Benchmark — Bombarde Telegram + Electron WS en parallele.

Usage:
    python benchmark_dual.py                # 20 questions chaque canal
    python benchmark_dual.py --count 50     # 50 questions chaque
    python benchmark_dual.py --telegram     # Telegram seulement
    python benchmark_dual.py --electron     # Electron seulement
"""

import asyncio
import json
import time
import sys
import os
import argparse
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# === PROMPTS DE BOMBARDEMENT ===
PROMPTS = [
    # Questions LLM variees
    "Bonjour, comment tu vas?",
    "Quelle est la capitale du Japon?",
    "Explique le machine learning en 2 phrases",
    "C'est quoi Docker?",
    "Donne 3 avantages de Python",
    "Qui a invente internet?",
    "Combien de planetes dans le systeme solaire?",
    "C'est quoi une API REST?",
    "Explique la blockchain simplement",
    "Quelle est la distance Terre-Lune?",
    # Commandes vocales (Commander doit matcher)
    "ouvre chrome",
    "volume a 50",
    "quelle heure",
    "cherche rapport pdf",
    "lance le terminal",
    "batterie",
    "google python tutoriel",
    "youtube musique",
    "calcule 42 fois 13",
    "pile ou face",
    # Questions avancees
    "Compare Python et JavaScript en 3 points",
    "C'est quoi le GPU computing?",
    "Explique les microservices",
    "Comment fonctionne HTTPS?",
    "C'est quoi Kubernetes?",
    "Donne une astuce Git utile",
    "Quel est le meilleur framework web Python?",
    "Explique le concept de conteneurisation",
    "C'est quoi le edge computing?",
    "Comment optimiser une base de donnees?",
    # Edge cases
    "merci",
    "ok",
    "hmm",
    "aide",
    "repete",
    "fais un truc cool",
    "raconte une blague",
    "quelle est ta couleur preferee?",
    "tu connais GPT?",
    "donne moi un conseil",
]


def _score(text: str, latency: float) -> int:
    """Score rapide: qualite + vitesse."""
    if not text or len(text) < 2:
        return 0
    score = 0
    # French
    fr = ["je", "le", "la", "de", "du", "un", "est", "les", "des", "en"]
    if sum(1 for m in fr if f" {m} " in f" {text.lower()} ") >= 2:
        score += 25
    elif len(text) > 5:
        score += 10
    # Length
    words = len(text.split())
    if 3 <= words <= 200:
        score += 25
    elif words > 0:
        score += 10
    # No leaks
    if "<think>" not in text and "/nothink" not in text:
        score += 20
    if "Tu es JARVIS" not in text and "sandbox" not in text.lower():
        score += 10
    # Speed
    if latency < 2:
        score += 20
    elif latency < 5:
        score += 10
    elif latency < 10:
        score += 5
    return min(score, 100)


# ========== TELEGRAM ==========
async def send_telegram(token: str, chat_id: int, text: str) -> tuple:
    """Envoie un message Telegram et attend la reponse du bot."""
    import httpx

    t0 = time.time()

    # Envoyer le message
    async with httpx.AsyncClient(timeout=5) as client:
        await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )

    # Attendre la reponse du bot (polling getUpdates)
    reply = None
    for attempt in range(20):  # 20 x 1.5s = 30s max
        await asyncio.sleep(1.5)
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"limit": 5, "offset": -5},
            )
            data = resp.json()
            if data.get("ok"):
                for upd in reversed(data.get("result", [])):
                    msg = upd.get("message", {})
                    # Bot reply = from bot (is_bot=True) or reply to our message
                    from_user = msg.get("from", {})
                    msg_text = msg.get("text", "")
                    if from_user.get("is_bot") and msg_text and msg_text != text:
                        reply = msg_text
                        break
            if reply:
                break

    latency = time.time() - t0
    return reply, latency


# ========== ELECTRON (3 endpoints) ==========
async def send_electron_collab(text: str) -> tuple:
    """POST /api/collab/ask — reponse collaborative rapide."""
    import httpx
    t0 = time.time()
    reply = None
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "http://127.0.0.1:9742/api/collab/ask",
                json={"prompt": text},
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data.get("response", "")
                latency_ms = data.get("latency_ms", 0)
    except Exception as e:
        reply = f"[ERROR] {e}"
    latency = time.time() - t0
    return reply, latency


async def send_electron_telegram(text: str) -> tuple:
    """POST /api/telegram/chat — simule un message Telegram via Electron."""
    import httpx
    t0 = time.time()
    reply = None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "http://127.0.0.1:9742/api/telegram/chat",
                json={"text": text},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    inner = data.get("data", {})
                    reply = inner.get("text", "")
                else:
                    reply = f"[ERR:{data.get('error', '?')[:60]}]"
            elif resp.status_code == 500:
                data = resp.json()
                reply = f"[500:{data.get('error', '?')[:60]}]"
    except Exception as e:
        reply = f"[ERROR] {e}"
    latency = time.time() - t0
    return reply, latency


async def send_electron_race(text: str) -> tuple:
    """POST /api/orchestrate/race — race M1/M2/M3 via Electron."""
    import httpx
    t0 = time.time()
    reply = None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "http://127.0.0.1:9742/api/orchestrate/race",
                json={"prompt": text, "pattern": "simple"},
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", "").strip()
                # Strip thinking tags
                import re
                content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
                if content:
                    reply = content
    except Exception as e:
        reply = f"[ERROR] {e}"
    latency = time.time() - t0
    return reply, latency


# ========== BENCHMARK ==========
async def benchmark_channel(name: str, send_fn, prompts: list, verbose: bool) -> dict:
    """Benchmark un canal (Telegram ou Electron)."""
    results = {
        "channel": name,
        "total": len(prompts),
        "success": 0,
        "fail": 0,
        "scores": [],
        "latencies": [],
        "errors": [],
    }

    for i, prompt in enumerate(prompts):
        try:
            reply, latency = await send_fn(prompt)
            if reply and not reply.startswith("["):
                results["success"] += 1
                sc = _score(reply, latency)
                results["scores"].append(sc)
                results["latencies"].append(latency)
                short = reply[:60].replace("\n", " ")
                if verbose:
                    print(f"  [{name:4s}] [{i+1:2d}/{len(prompts)}] {latency:5.1f}s {sc:3d}/100 | {prompt[:25]:25s} -> {short}")
            else:
                results["fail"] += 1
                results["errors"].append({"prompt": prompt, "reply": reply})
                if verbose:
                    print(f"  [{name:4s}] [{i+1:2d}/{len(prompts)}] FAIL | {prompt[:40]} -> {reply}")
        except Exception as e:
            results["fail"] += 1
            results["errors"].append({"prompt": prompt, "error": str(e)})
            if verbose:
                print(f"  [{name:4s}] [{i+1:2d}/{len(prompts)}] ERR  | {prompt[:40]} -> {e}")

    return results


def print_report(results: list):
    """Affiche le rapport final."""
    print("\n" + "=" * 70)
    print("  JARVIS DUAL BENCHMARK — Telegram + Electron")
    print("=" * 70)

    for r in results:
        name = r["channel"]
        total = r["total"]
        ok = r["success"]
        fail = r["fail"]
        avg_sc = sum(r["scores"]) / max(len(r["scores"]), 1)
        avg_lat = sum(r["latencies"]) / max(len(r["latencies"]), 1)
        min_lat = min(r["latencies"]) if r["latencies"] else 0
        max_lat = max(r["latencies"]) if r["latencies"] else 0
        pct = 100 * ok / max(total, 1)

        print(f"\n  [{name}]")
        print(f"    Total: {total} | Success: {ok} ({pct:.0f}%) | Fail: {fail}")
        print(f"    Score: {avg_sc:.1f}/100 | Latence: {avg_lat:.1f}s (min={min_lat:.1f}s, max={max_lat:.1f}s)")

        if r["errors"]:
            print(f"    Erreurs:")
            for err in r["errors"][:5]:
                print(f"      - {err.get('prompt', '?')[:40]} -> {err.get('reply', err.get('error', '?'))[:60]}")

    # Comparaison multi-canaux
    if len(results) >= 2:
        print(f"\n  --- Classement ---")
        ranked = []
        for r in results:
            avg_sc = sum(r["scores"]) / max(len(r["scores"]), 1)
            avg_lat = sum(r["latencies"]) / max(len(r["latencies"]), 1)
            pct = 100 * r["success"] / max(r["total"], 1)
            ranked.append((r["channel"], avg_sc, avg_lat, pct))
        ranked.sort(key=lambda x: (-x[1], x[2]))  # best score, then fastest
        for i, (ch, sc, lat, pct) in enumerate(ranked):
            medal = ["1er", "2e", "3e", "4e"][i] if i < 4 else f"{i+1}e"
            print(f"    {medal}: {ch:5s} | {sc:.1f}/100 | {lat:.1f}s | {pct:.0f}%")

    print("\n" + "=" * 70)


async def main():
    parser = argparse.ArgumentParser(description="JARVIS Dual Benchmark")
    parser.add_argument("--count", type=int, default=20, help="Nombre de questions par canal")
    parser.add_argument("--telegram", action="store_true", help="Telegram seulement")
    parser.add_argument("--electron", action="store_true", help="Electron seulement")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")
    args = parser.parse_args()

    # Charger config Telegram
    with open("C:/Users/franc/.openclaw/openclaw.json") as f:
        cfg = json.load(f)
    tg_token = cfg["channels"]["telegram"]["botToken"]
    tg_chat = cfg["channels"]["telegram"]["allowFrom"][0]

    prompts = PROMPTS[:args.count]
    do_telegram = not args.electron or args.telegram
    do_electron = not args.telegram or args.electron
    if not args.telegram and not args.electron:
        do_telegram = do_electron = True

    print(f"\n  JARVIS Dual Benchmark")
    print(f"  Prompts: {len(prompts)} | Telegram: {'ON' if do_telegram else 'OFF'} | Electron: {'ON' if do_electron else 'OFF'}")
    print(f"  {'-' * 50}\n")

    results = []

    # Electron endpoints (3 canaux)
    if do_electron:
        print("  --- Electron /api/collab/ask ---")
        r = await benchmark_channel("COLAB", send_electron_collab, prompts, args.verbose)
        results.append(r)

        print("\n  --- Electron /api/telegram/chat ---")
        r = await benchmark_channel("E-TG", send_electron_telegram, prompts, args.verbose)
        results.append(r)

        print("\n  --- Electron /api/orchestrate/race ---")
        r = await benchmark_channel("RACE", send_electron_race, prompts, args.verbose)
        results.append(r)

    # Telegram reel (envoi + polling reponse)
    if do_telegram:
        print("\n  --- Telegram reel (@turboSSebot via OpenClaw) ---")
        telegram_fn = lambda text, t=tg_token, c=tg_chat: send_telegram(t, c, text)
        r = await benchmark_channel("TG", telegram_fn, prompts, args.verbose)
        results.append(r)

    print_report(results)


if __name__ == "__main__":
    asyncio.run(main())
