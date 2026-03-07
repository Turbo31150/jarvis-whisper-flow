"""
JARVIS Cluster Bridge — Connecte jarvis-whisper-flow au cluster IA (M1/OL1)
et au dispatcher cowork (395 scripts autonomes).

Pipeline: Voix → Whisper → Commander → Skills/Cluster → TTS
"""

import asyncio
import json
import re
import logging
from typing import Optional

logger = logging.getLogger("jarvis.cluster")

# Cluster nodes
NODES = {
    "M1": {
        "url": "http://127.0.0.1:1234/v1/chat/completions",
        "model": "qwen3-8b",
        "timeout": 12,
        "system": "/nothink\nTu es JARVIS, assistant de Turbo. Francais, concis 2-3 phrases.",
        "max_tokens": 200,
    },
    "OL1": {
        "url": "http://127.0.0.1:11434/api/chat",
        "model": "qwen3:1.7b",
        "timeout": 12,
        "system": "Tu es JARVIS. Francais, concis.",
        "max_tokens": 200,
    },
}

THINK_RE = re.compile(r'<think>[\s\S]*?</think>')


async def _http_post(url: str, payload: dict, timeout: float) -> Optional[dict]:
    """HTTP POST via httpx (preferred) or curl fallback."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json()
    except ImportError:
        # Fallback: curl subprocess
        import tempfile, os
        body = json.dumps(payload)
        # Write body to temp file to avoid shell escaping issues on Windows
        fd, tmp = tempfile.mkstemp(suffix=".json")
        try:
            os.write(fd, body.encode("utf-8"))
            os.close(fd)
            proc = await asyncio.create_subprocess_exec(
                "curl", "-s", "--max-time", str(int(timeout)),
                url,
                "-H", "Content-Type: application/json",
                "-d", f"@{tmp}",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 3)
            return json.loads(stdout.decode("utf-8"))
        finally:
            os.unlink(tmp)
    except Exception as e:
        logger.debug(f"HTTP POST {url} failed: {e}")
    return None


async def query_m1(prompt: str, system: str = None) -> Optional[str]:
    """Query M1 via LM Studio OpenAI-compat API."""
    node = NODES["M1"]
    sys_prompt = system or node["system"]
    payload = {
        "model": node["model"],
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": node["max_tokens"],
        "stream": False,
    }
    try:
        data = await _http_post(node["url"], payload, node["timeout"])
        if data:
            text = data["choices"][0]["message"]["content"]
            text = THINK_RE.sub('', text).strip()
            return text if len(text) > 1 else None
    except Exception as e:
        logger.warning(f"M1 query failed: {e}")
    return None


async def query_ol1(prompt: str, system: str = None) -> Optional[str]:
    """Query OL1 via Ollama API."""
    node = NODES["OL1"]
    sys_prompt = system or node["system"]
    payload = {
        "model": node["model"],
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "think": False,
        "options": {"num_predict": node["max_tokens"]},
    }
    try:
        data = await _http_post(node["url"], payload, node["timeout"])
        if data:
            text = data["message"]["content"]
            text = THINK_RE.sub('', text).strip()
            return text if len(text) > 1 else None
    except Exception as e:
        logger.warning(f"OL1 query failed: {e}")
    return None


async def cluster_race(prompt: str, system: str = None) -> tuple[Optional[str], str]:
    """Race M1 vs OL1 — first good response wins.
    Returns (response_text, agent_name).
    """
    async def _m1():
        r = await query_m1(prompt, system)
        return (r, "M1") if r else None

    async def _ol1():
        r = await query_ol1(prompt, system)
        return (r, "OL1") if r else None

    tasks = [asyncio.create_task(_m1()), asyncio.create_task(_ol1())]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result:
            # Cancel remaining
            for t in tasks:
                t.cancel()
            return result

    return (None, "NONE")


async def dispatch_cowork(query: str, cowork_path: str = "F:/BUREAU/jarvis-cowork") -> Optional[str]:
    """Dispatch a query to cowork scripts via the cowork dispatcher."""
    import sys
    dispatcher = f"{cowork_path}/cowork_dispatcher.py"
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, dispatcher, "--query", query, "--once",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
            cwd=cowork_path,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode("utf-8", errors="replace").strip()
        if output:
            try:
                data = json.loads(output)
                return data.get("result") or data.get("output") or str(data)
            except json.JSONDecodeError:
                return output
    except Exception as e:
        logger.warning(f"Cowork dispatch failed: {e}")
    return None
