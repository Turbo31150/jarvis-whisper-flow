#!/usr/bin/env python3
"""Quick Telegram bombardment test."""
import asyncio, time, sys, os, json

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

with open("C:/Users/franc/.openclaw/openclaw.json") as f:
    cfg = json.load(f)
TOKEN = cfg["channels"]["telegram"]["botToken"]
CHAT = cfg["channels"]["telegram"]["allowFrom"][0]

PROMPTS = [
    "Salut JARVIS, ca va?",
    "Quelle heure est-il?",
    "Explique Docker en 2 phrases",
    "Combien font 42 x 13?",
    "C est quoi Python?",
    "Donne 3 conseils pour coder",
    "Quelle est la capitale de la France?",
    "Comment fonctionne un SSD?",
    "Raconte une blague",
    "Merci JARVIS",
]

import httpx


async def send_tg(text):
    async with httpx.AsyncClient(timeout=5) as c:
        await c.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT, "text": text},
        )


async def query_proxy(text):
    """Query canvas proxy /chat (same backend as OpenClaw Telegram)."""
    async with httpx.AsyncClient(timeout=30) as c:
        resp = await c.post(
            "http://127.0.0.1:18800/chat",
            json={"text": text, "agent": "telegram"},
        )
        data = resp.json()
        if data.get("ok"):
            return data.get("data", {}).get("text", "")
    return None


async def run():
    print("  Telegram Bombardement (10 messages)")
    print("  Canal 1: Envoi reel Telegram | Canal 2: Proxy /chat (meme backend)")
    print("  " + "-" * 60)

    ok_tg = 0
    ok_proxy = 0
    for i, p in enumerate(PROMPTS):
        # Envoyer sur Telegram (fire-and-forget, OpenClaw repondra)
        t0 = time.time()
        await send_tg(p)
        tg_lat = time.time() - t0
        ok_tg += 1  # Message envoye

        # Obtenir la reponse via proxy /chat (meme modele OL1)
        t0 = time.time()
        try:
            reply = await query_proxy(p)
            lat = time.time() - t0
            if reply:
                ok_proxy += 1
                short = reply[:55].replace("\n", " ")
                print(f"  [{i+1:2d}] OK  {lat:5.1f}s | {p[:25]:25s} -> {short}")
            else:
                print(f"  [{i+1:2d}] FAIL {lat:5.1f}s | {p[:25]:25s} -> (empty)")
        except Exception as e:
            lat = time.time() - t0
            print(f"  [{i+1:2d}] ERR  {lat:5.1f}s | {p[:25]:25s} -> {e}")

    print(f"\n  Telegram envoyes: {ok_tg}/{len(PROMPTS)}")
    print(f"  Proxy reponses:  {ok_proxy}/{len(PROMPTS)}")


asyncio.run(run())
